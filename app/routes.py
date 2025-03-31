from flask import render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
from app import app
from datetime import datetime
import logging
logging.basicConfig(level=logging.DEBUG)


# MySQL-Verbindung (einfache Variante)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="faktura_user",
        password="meinpasswort",
        database="faktura_app"
    )

def user_has_role(role_name):
    if 'user_id' not in session:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 1 FROM user_roles ur
        JOIN rollen r ON ur.rollen_id = r.id
        WHERE ur.user_id = %s AND r.bezeichnung = %s
        LIMIT 1
    """
    cursor.execute(query, (session['user_id'], role_name))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result is not None


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

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
            # ➕ Login-Zeit speichern
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('home'))
        else:
            return "Login fehlgeschlagen", 401

    return render_template('login.html')


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
        return redirect(url_for('home'))  # oder ein "403 Zugriff verweigert"-Template

    # Datenbankverbindung und Abruf (hier nur Dummy-Text)
    return "📄 Bürgschaften-Übersicht (Platzhalter)"
