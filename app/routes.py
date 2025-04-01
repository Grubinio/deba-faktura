from flask import render_template, request, redirect, session, url_for, jsonify, Response, flash
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
from app import app
import os
from app.forms import LoginForm  
from decimal import Decimal
from datetime import datetime
from mysql.connector.pooling import MySQLConnectionPool
import logging
logging.basicConfig(
    filename='/var/www/faktura/error.log',
    level=logging.DEBUG,  # oder ERROR, wenn du nur Fehler willst
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

##DB Connection pooling
pool = MySQLConnectionPool(
    pool_name=app.config['DB_POOL_NAME'],
    pool_size=app.config['DB_POOL_SIZE'],
    host=app.config['DB_HOST'],
    user=app.config['DB_USER'],
    password=app.config['DB_PASSWORD'],
    database=app.config['DB_NAME']
)
## DB Connection
def get_db_connection():
    try:
        return pool.get_connection()
    except mysql.connector.Error as err:
        app.logger.error(f"DB-Verbindungsfehler: {err}")
        raise

##Userrollen für Zugriff
def user_has_role(role_name):
    if 'user_id' not in session:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 1 FROM user_roles ur
            JOIN rollen r ON ur.rollen_id = r.id
            WHERE ur.user_id = %s AND r.bezeichnung = %s
            LIMIT 1
        """, (session['user_id'], role_name))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


@app.context_processor
def inject_user_role_check():
    return dict(user_has_role=user_has_role)


@app.route('/')
def index():
    return redirect(url_for('login'))

##Login
from app.forms import LoginForm  # Oben importieren

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user'] = user['username']
            session['user_id'] = user['id']
            session['vorname'] = user['vorname']
            session['nachname'] = user['nachname']

            # Login-Zeit speichern
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('home'))
        else:
            flash("❌ Login fehlgeschlagen", "danger")
            return redirect(url_for('login'))

    return render_template('login.html', form=form)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))  # Zugriff nur für Admin

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        funktion = request.form['funktion']

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, funktion)
                VALUES (%s, %s, %s, %s)
            """, (username, hashed_password, email, funktion))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('admin_dashboard'))  # oder zurück zum Login
        except mysql.connector.IntegrityError:
            return "Benutzername existiert bereits!", 409

    return render_template('register.html')


@app.route('/home')
def home():
    if 'user' in session:
        # 🕒 Aktuelle Stunde
        stunde = datetime.now().hour
        if stunde < 7:
            begruessung ="Guten Morgen Frühaufsteher"
        elif stunde < 10:
            begruessung = "Guten Morgen"
        elif stunde < 14:
            begruessung = "Guten Tag"
        elif stunde < 17:
            begruessung = "Guten Nachmittag"
        else:
            begruessung = "Guten Abend"
        return render_template('home.html', begruessung=begruessung, user=session['user'], vorname=session['vorname'],nachname=session['nachname'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if not user_has_role('Admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, email, funktion, last_login FROM users ORDER BY id ASC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin.html', users=users)

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not user_has_role('Admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not user_has_role('Admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        funktion = request.form['funktion']

        cursor.execute("""
            UPDATE users SET username = %s, email = %s, funktion = %s WHERE id = %s
        """, (username, email, funktion, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit_user.html', user=user)

@app.route('/auftrag/<int:auftrag_id>')
def auftrag_detail(auftrag_id):
    return f"Details für Auftrag #{auftrag_id} (Platzhalter)"

@app.route('/kunde/<int:kunde_id>')
def kunde_detail(kunde_id):
    return f"Details für Kunde #{kunde_id} (Platzhalter)"

@app.route('/auftrag/neuer')
def neuer_auftrag():
    return "Neuen Auftrag anlegen (Platzhalter)"

@app.route('/auftrag/filter')
def filter_auftraege():
    return "Aufträge filtern (Platzhalter)"

@app.route('/buergschaften')
def buergschaften():
    if not any(user_has_role(r) for r in ['Fakturierung', 'Management', 'Superuser']):
        return redirect(url_for('home'))

    auftragsnummer = request.args.get('auftragsnummer', '').strip()
    buerge = request.args.get('buerge', '')
    art = request.args.get('art', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Filter aufbauen
    sql = """
        SELECT 
            b.id,
            b.buergschaftsnummer,
            b.auftragsnummer,
            a.bezeichnung_kurz,
            b.surety,
            b.buergschaftsart,
            b.buergschaftssumme,
            b.buergschaftssumme_aktuell,
            b.erstelldatum,
            b.voraussichtliche_rueckgabe,
            CASE 
                WHEN b.buergschaftssumme_aktuell = 0 THEN 'Ausgebucht'
                WHEN b.buergschaftssumme_aktuell < b.buergschaftssumme THEN 'Teilweise ausgebucht'
                ELSE 'Aktiv'
            END AS status
        FROM buergschaften b
        LEFT JOIN auftraege a ON b.auftragsnummer = a.auftragsnummer
        WHERE 1=1
    """

    params = []

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

    # Alle Bürgen für Dropdown
    cursor.execute("SELECT DISTINCT buergenname FROM sureties ORDER BY buergenname")
    buergen_liste = [row['buergenname'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template('buergschaften.html', buergschaften=buergschaften,
                           filter_auftragsnummer=auftragsnummer,
                           filter_buerge=buerge,
                           filter_art=art,
                           buergen_liste=buergen_liste)


@app.route('/buergschaften/<int:buergschaft_id>')
def buergschaft_detail(buergschaft_id):
    if not any(user_has_role(r) for r in ['Fakturierung', 'Management', 'Superuser']):
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Bürgschaft abrufen
    cursor.execute("""
        SELECT 
            b.*, 
            a.bezeichnung_kurz 
        FROM buergschaften b
        LEFT JOIN auftraege a ON b.auftragsnummer = a.auftragsnummer
        WHERE b.id = %s
    """, (buergschaft_id,))
    buergschaft = cursor.fetchone()

    if not buergschaft:
        cursor.close()
        conn.close()
        return "Bürgschaft nicht gefunden", 404

    # Ausbuchungen abrufen
    cursor.execute("""
        SELECT * FROM buergschaften_ausbuchungen
        WHERE buergschaftsnummer = %s
        ORDER BY ausbuchung DESC
    """, (buergschaft['buergschaftsnummer'],))
    ausbuchungen = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("buergschaft_detail.html",
                           buergschaft=buergschaft,
                           ausbuchungen=ausbuchungen)

@app.route('/buergschaften/<int:buergschaft_id>/ausbuchung', methods=['GET', 'POST'])
def buergschaft_ausbuchung(buergschaft_id):
    if not user_has_role('Fakturierung'):
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Bürgschaft holen
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

            # Betrag als Decimal einlesen
            summe_decimal = Decimal(summe.replace('.', '').replace(',', '.'))

            # Validierung
            if summe_decimal <= 0:
                raise ValueError("Summe muss positiv sein.")
            if buergschaft['buergschaftssumme_aktuell'] is not None and summe_decimal > buergschaft['buergschaftssumme_aktuell']:
                flash("❌ Die Ausbuchung darf den Restbetrag nicht überschreiten!", "danger")
                raise ValueError("Die Ausbuchung übersteigt den Restbetrag.")

            # Ausbuchung einfügen
            cursor.execute("""
                INSERT INTO buergschaften_ausbuchungen (buergschaftsnummer, ausbuchungssumme, ausbuchung, bemerkung)
                VALUES (%s, %s, %s, %s)
            """, (buergschaft['buergschaftsnummer'], summe_decimal, datum, bemerkung))

            # Restbetrag aktualisieren
            new_rest = Decimal(buergschaft['buergschaftssumme_aktuell']) - summe_decimal
            cursor.execute("""
                UPDATE buergschaften SET buergschaftssumme_aktuell = %s WHERE id = %s
            """, (new_rest, buergschaft_id))

            conn.commit()
            flash("✅ Ausbuchung erfolgreich hinzugefügt!", "success")
            return redirect(url_for('buergschaft_detail', buergschaft_id=buergschaft_id))

        except Exception as e:
            conn.rollback()
            flash(f"❗ Fehler: {str(e)}", "danger")
            app.logger.error(f"Fehler beim Speichern der Bürgschaft: {str(e)}")

    cursor.close()
    conn.close()
    return render_template("buergschaft_ausbuchung.html", buergschaft=buergschaft)


@app.route('/buergschaften/add', methods=['GET', 'POST'])
def buergschaft_add():
    if not any(user_has_role(r) for r in ['Fakturierung', 'Superuser']):
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Nur Aufträge ohne 'Schlussrechnung'
    cursor.execute("""
        SELECT auftragsnummer, bezeichnung_kurz
        FROM auftraege
        WHERE status != 'Schlussrechnung'
        ORDER BY auftragsnummer DESC
    """)
    auftraege = cursor.fetchall()

    # Sureties für Combobox
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
            rueckgabe = data['voraussichtliche_rueckgabe']
            rueckgabe = datetime.strptime(rueckgabe, "%d.%m.%Y").date() if rueckgabe else None
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
            """, (
                bnr, anr, beguenstigter, surety, erstelldatum, rueckgabe,
                art, summe, summe, waehrung, bemerkung
            ))

            conn.commit()
            flash("✅ Bürgschaft erfolgreich gespeichert.", "success")
            return redirect(url_for('buergschaften'))
        except Exception as e:
            conn.rollback()
            flash(f"❗ Fehler: {str(e)}", "danger")
            app.logger.error(f"Fehler beim Speichern der Bürgschaft: {str(e)}")

    cursor.close()
    conn.close()
    return render_template(
        'buergschaft_add.html',
        auftraege=auftraege,
        buergen=buergen,
        now=datetime.today().strftime("%d.%m.%Y")
    )


@app.route('/api/beguenstigter/<auftragsnummer>')
def api_beguenstigter(auftragsnummer):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT k.firmenname
        FROM auftraege a
        JOIN kunden k ON a.kundennummer = k.kundennummer
        WHERE a.auftragsnummer = %s
    """, (auftragsnummer,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result and result['firmenname']:
        return Response(result['firmenname'], mimetype="text/plain")
    else:
        return Response("Nicht gefunden", status=404, mimetype="text/plain")

@app.route("/ping")
def ping():
    return "pong"