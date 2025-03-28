from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'dein_sicherer_key'

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
            return redirect(url_for('home'))
        else:
            return "Login fehlgeschlagen", 401

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))  # oder: return "Zugriff verweigert", 403

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
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
    cursor.execute("SELECT id, username FROM users ORDER BY id ASC")
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
