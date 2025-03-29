from flask import render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
from app import app

# MySQL-Verbindung (einfache Variante)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="faktura_user",
        password="meinpasswort",
        database="faktura_app"
    )

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
        return render_template('home.html', user=session['user'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if 'user' not in session or session['user'] != 'admin':
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
    if 'user' not in session or session['user'] != 'admin':
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
    if 'user' not in session or session['user'] != 'admin':
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
