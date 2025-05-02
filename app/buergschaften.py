# app/buergschaften.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response
from app.db_pool import get_db_connection
from decimal import Decimal
from datetime import datetime

buergschaften_bp = Blueprint('buergschaften', __name__)

from app.utils import user_has_role

@buergschaften_bp.route('/buergschaften')
def buergschaften():
    if not any(user_has_role(r) for r in ['Fakturierung', 'Management', 'Superuser']):
        return redirect(url_for('home'))
    
    auftragsnummer = request.args.get('auftragsnummer', '').strip()
    buerge = request.args.get('buerge', '')
    art = request.args.get('art', '')
    zeige_alle = request.args.get('zeige_alle', '') == '1'

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT 
            b.id, b.buergschaftsnummer, b.auftragsnummer, a.bezeichnung_kurz, b.surety,
            b.buergschaftsart, b.buergschaftssumme, b.buergschaftssumme_aktuell,
            b.erstelldatum, b.voraussichtliche_rueckgabe,
            CASE 
                WHEN b.buergschaftssumme_aktuell = 0 THEN 'Ausgebucht'
                WHEN b.buergschaftssumme_aktuell < b.buergschaftssumme THEN 'Teilweise ausgebucht'
                ELSE 'Aktiv' END AS status
        FROM buergschaften b
        LEFT JOIN auftraege a ON b.auftragsnummer = a.auftragsnummer
        WHERE 1=1
    """
    params = []
    if not zeige_alle:
        sql += " AND (b.buergschaftssumme_aktuell IS NULL OR b.buergschaftssumme_aktuell > 0)"
    if auftragsnummer:
        sql += " AND b.auftragsnummer LIKE %s"
        params.append(f"%{auftragsnummer}%")
    if buerge:
        sql += " AND b.surety = %s"
        params.append(buerge)
    if art:
        sql += " AND b.buergschaftsart = %s"
        params.append(art)

    sql += " ORDER BY b.erstelldatum DESC"

    cursor.execute(sql, params)
    buergschaften = cursor.fetchall()

    cursor.execute("SELECT DISTINCT buergenname FROM sureties ORDER BY buergenname")
    buergen_liste = [row['buergenname'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template('buergschaften.html', buergschaften=buergschaften, 
                           filter_auftragsnummer=auftragsnummer, filter_buerge=buerge, 
                           filter_art=art, buergen_liste=buergen_liste, zeige_alle=zeige_alle)


@buergschaften_bp.route('/buergschaften/add', methods=['GET', 'POST'])
def buergschaft_add():
    if not any(user_has_role(r) for r in ['Fakturierung', 'Superuser']):
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT auftragsnummer, bezeichnung_kurz FROM auftraege WHERE status != 'Schlussrechnung'
        ORDER BY auftragsnummer DESC
    """)
    auftraege = cursor.fetchall()
    cursor.execute("SELECT DISTINCT buergenname FROM sureties ORDER BY buergenname")
    buergen = [row['buergenname'] for row in cursor.fetchall()]

    if request.method == 'POST':
        try:
            data = request.form
            bnr = data['buergschaftsnummer'].strip()
            anr = data['auftragsnummer']
            beguenstigter = data['beguenstigter'].strip()
            surety = data['surety']
            erstelldatum = datetime.strptime(data['erstelldatum'], "%d.%m.%Y").date()
            rueckgabe = datetime.strptime(data['voraussichtliche_rueckgabe'], "%d.%m.%Y").date() if data['voraussichtliche_rueckgabe'] else None
            art = data['buergschaftsart']
            summe = float(data['buergschaftssumme'].replace('.', '').replace(',', '.'))
            waehrung = data['waehrung']
            bemerkung = data['bemerkung'].strip() or None

            cursor.execute("""
                INSERT INTO buergschaften (
                    buergschaftsnummer, auftragsnummer, beguenstigter, surety,
                    erstelldatum, voraussichtliche_rueckgabe,
                    buergschaftsart, buergschaftssumme, buergschaftssumme_aktuell,
                    waehrung, bemerkung
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (bnr, anr, beguenstigter, surety, erstelldatum, rueckgabe, art, summe, summe, waehrung, bemerkung))
            conn.commit()
            flash("✅ Bürgschaft erfolgreich gespeichert.", "success")
            return redirect(url_for('buergschaften.buergschaften'))
        except Exception as e:
            conn.rollback()
            flash(f"❗ Fehler: {str(e)}", "danger")

    cursor.close()
    conn.close()
    return render_template('buergschaft_add.html', auftraege=auftraege, buergen=buergen, now=datetime.today().strftime("%d.%m.%Y"))

@buergschaften_bp.route('/buergschaften/<int:buergschaft_id>')
def buergschaft_detail(buergschaft_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM buergschaften WHERE id = %s
    """, (buergschaft_id,))
    buergschaft = cursor.fetchone()

    cursor.close()
    conn.close()

    if not buergschaft:
        flash("Bürgschaft nicht gefunden.", "danger")
        return redirect(url_for('buergschaften.buergschaften'))

    return render_template('buergschaft_detail.html', buergschaft=buergschaft)

@buergschaften_bp.route('/buergschaften/<int:buergschaft_id>/ausbuchung', methods=['GET', 'POST'])
def buergschaft_ausbuchung(buergschaft_id):
    if not user_has_role('Fakturierung'):
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM buergschaften WHERE id = %s", (buergschaft_id,))
    buergschaft = cursor.fetchone()

    if not buergschaft:
        cursor.close()
        conn.close()
        return "Bürgschaft nicht gefunden", 404

    if request.method == 'POST':
        try:
            summe = request.form.get('ausbuchungssumme')
            datum_str = request.form.get('ausbuchung')
            datum = datetime.strptime(datum_str, "%d.%m.%Y").date()
            bemerkung = request.form.get('bemerkung', '')

            summe_decimal = Decimal(summe.replace('.', '').replace(',', '.'))

            if summe_decimal <= 0:
                raise ValueError("Summe muss positiv sein.")
            if buergschaft['buergschaftssumme_aktuell'] is not None and summe_decimal > buergschaft['buergschaftssumme_aktuell']:
                flash("❌ Die Ausbuchung darf den Restbetrag nicht überschreiten!", "danger")
                raise ValueError("Die Ausbuchung übersteigt den Restbetrag.")

            cursor.execute("""
                INSERT INTO buergschaften_ausbuchungen (buergschaftsnummer, ausbuchungssumme, ausbuchung, bemerkung)
                VALUES (%s, %s, %s, %s)
            """, (buergschaft['buergschaftsnummer'], summe_decimal, datum, bemerkung))

            new_rest = Decimal(buergschaft['buergschaftssumme_aktuell']) - summe_decimal
            cursor.execute("""
                UPDATE buergschaften SET buergschaftssumme_aktuell = %s WHERE id = %s
            """, (new_rest, buergschaft_id))

            conn.commit()
            flash("✅ Ausbuchung erfolgreich hinzugefügt!", "success")
            return redirect(url_for('buergschaften.buergschaft_detail', buergschaft_id=buergschaft_id))

        except Exception as e:
            conn.rollback()
            flash(f"❗ Fehler: {str(e)}", "danger")

    cursor.close()
    conn.close()
    return render_template("buergschaft_ausbuchung.html", buergschaft=buergschaft)