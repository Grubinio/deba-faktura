# app/auth.py
from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from app.db import get_db_connection
from app.forms import LoginForm, RegisterForm


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
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

            # Login-Zeit aktualisieren
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('home'))  # ACHTUNG: 'main.home' wenn dein home-View später in main.py liegt
        else:
            flash("❌ Login fehlgeschlagen", "danger")
            return redirect(url_for('auth.login'))

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('auth.login'))

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        funktion = form.funktion.data

        hashed_password = generate_password_hash(password)

        # TODO: Registrierung speichern (bei Bedarf)
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # ...

        flash("✅ Registrierung erfolgreich!", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

# app/auth.py

# Blueprint wird exportiert für __init__.py
__all__ = ['auth_bp']

