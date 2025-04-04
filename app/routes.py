from flask import render_template, request, redirect, session, url_for, jsonify, Response, flash
from app import app
from app.forms import DeleteUserForm
from decimal import Decimal
from datetime import datetime
import logging
from app.db import get_db_connection

# Logging
logging.basicConfig(
    filename='/var/www/faktura/error.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# DEBUG-Modus
app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

# --- Zugriffskontrolle ---
def user_has_role(role_name):
    if 'user_id' not in session:
        return False

    from app.db import get_db_connection
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

# --- Start & Home ---
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

@app.route('/home', endpoint='home')
def home():
    if 'user' in session:
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
        return render_template(
            'home.html',
            begruessung=begruessung,
            user=session['user'],
            vorname=session['vorname'],
            nachname=session['nachname']
        )
    return redirect(url_for('auth.login'))


# --- Weitere Routen (Platzhalter & API) ---
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

@app.route('/api/beguenstigter/<auftragsnummer>')
def api_beguenstigter(auftragsnummer):
    from app.db import get_db_connection
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

@app.route('/impressum')
def impressum():
    return render_template('impressum.html')
