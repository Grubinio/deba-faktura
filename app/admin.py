# app/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_db_connection
from app.forms import DeleteUserForm
from flask_wtf import FlaskForm
from wtforms import HiddenField

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

admin_bp = Blueprint('admin', __name__)

class DummyDeleteForm(FlaskForm):
    dummy = HiddenField()  # oder einfach leer lassen, nur für CSRF

@admin_bp.route('/admin')
def admin_dashboard():
    if not user_has_role('Admin'):
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            u.id, u.username, u.email, u.funktion, u.last_login,
            u.vorname, u.nachname,
            GROUP_CONCAT(r.bezeichnung SEPARATOR ', ') AS rollen
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN rollen r ON ur.rollen_id = r.id
        GROUP BY u.id
        ORDER BY u.id ASC
    """)
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    # CSRF-Löschformulare vorbereiten
    delete_forms = {user['id']: DeleteUserForm() for user in users}

    return render_template('admin.html', users=users, delete_forms=delete_forms)


@admin_bp.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not user_has_role('Admin'):
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Benutzer erfolgreich gelöscht.", "success")
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not user_has_role('Admin'):
        return redirect(url_for('auth.login'))

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

        flash("✅ Benutzer erfolgreich aktualisiert.", "success")
        return redirect(url_for('admin.admin_dashboard'))

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit_user.html', user=user)
