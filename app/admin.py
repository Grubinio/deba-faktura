# app/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.db import get_db_connection
from app.forms import DeleteUserForm, EditUserForm
from flask_wtf import FlaskForm
from wtforms import HiddenField
import traceback
from app.utils import admin_required

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

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        flash("❌ Benutzer nicht gefunden.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    form = EditUserForm(data=user)

    # Rollen laden
    cursor.execute("SELECT id, bezeichnung FROM rollen")
    rollen = cursor.fetchall()
    cursor.execute("SELECT rollen_id FROM user_roles WHERE user_id = %s", (user_id,))
    user_rollen = [r['rollen_id'] for r in cursor.fetchall()]

    if form.validate_on_submit():
        try:   
            # Verhindere, dass sich ein Admin selbst Adminrechte entzieht
            if user['id'] == session['user_id'] and 'Admin' not in request.form.getlist('rollen_name'):
                flash("❌ Du kannst dir selbst nicht die Admin-Rechte entziehen!", "danger")
                return redirect(url_for('admin.edit_user', user_id=user_id))

            cursor.execute("""
                UPDATE users
                SET username=%s, email=%s, funktion=%s,
                    geschlecht=%s, vorname=%s, nachname=%s
                WHERE id = %s
            """, (
                form.username.data,
                form.email.data,
                form.funktion.data,
                form.geschlecht.data,
                form.vorname.data,
                form.nachname.data,
                user_id
            ))
            # Rollen aktualisieren
            cursor.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
            rollen_ids = request.form.getlist('rollen')
            for rollen_id in rollen_ids:
                cursor.execute("INSERT INTO user_roles (user_id, rollen_id) VALUES (%s, %s)", (user_id, rollen_id))

            conn.commit()
            flash("✅ Benutzer erfolgreich aktualisiert.", "success")
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            conn.rollback()
            traceback.print_exc()  # schreibt vollständige Fehler-Traceback ins Terminal
            flash(f"❌ Fehler beim Speichern: {e}", "danger")
            return redirect(url_for('admin.edit_user', user_id=user_id))

    cursor.close()
    conn.close()

    return render_template('edit_user.html', form=form, user=user, rollen=rollen, user_rollen=user_rollen)

# admin.py
@admin_bp.route('/admin/update_roles/<int:user_id>', methods=['POST'])
def update_roles(user_id):
    if not user_has_role('Admin'):
        return jsonify(status='error', message='Nicht berechtigt')

    data = request.get_json()
    rolle_id = int(data.get('rolle_id'))
    aktiv = data.get('aktiv')

    # Verhindern, dass sich Admin selbst Admin-Rolle entzieht
    if user_id == session['user_id'] and not aktiv:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT bezeichnung FROM rollen WHERE id = %s", (rolle_id,))
        rolle = cursor.fetchone()
        if rolle and rolle['bezeichnung'] == 'Admin':
            return jsonify(status='error', message='Du kannst dir selbst nicht die Admin-Rolle entziehen!')

    conn = get_db_connection()
    cursor = conn.cursor()
    if aktiv:
        cursor.execute("REPLACE INTO user_roles (user_id, rollen_id) VALUES (%s, %s)", (user_id, rolle_id))
    else:
        cursor.execute("DELETE FROM user_roles WHERE user_id = %s AND rollen_id = %s", (user_id, rolle_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(status='ok')

@admin_bp.route('/admin/status')
@admin_required
def server_status():
    import psutil
    import shutil
    import platform
    import subprocess
    from datetime import datetime
    import flask
    import time

    # Festplatteninfo
    disk = shutil.disk_usage("/")
    disk_total = round(disk.total / (1024 ** 3), 1)
    disk_used = round(disk.used / (1024 ** 3), 1)
    disk_free = round(disk.free / (1024 ** 3), 1)
    disk_percent = int(disk.used / disk.total * 100)

    # RAM
    mem = psutil.virtual_memory()
    mem_total = round(mem.total / (1024 ** 3), 1)
    mem_used = round(mem.used / (1024 ** 3), 1)
    mem_percent = mem.percent

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)

    # Uptime
    uptime = subprocess.check_output("uptime -p", shell=True).decode().strip()

    # Systemzeit & Zeitzone
    system_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    timezone = time.tzname[0]

    # Python- und Flask-Version
    python_version = platform.python_version()
    flask_version = flask.__version__

    # Fail2Ban gebannte IPs
    try:
        raw_banned = subprocess.check_output("fail2ban-client status sshd | grep 'Banned IP list'", shell=True).decode().strip()
        banned_ips = raw_banned.replace("Banned IP list: ", "").strip()
        has_banned_ips = bool(banned_ips)
    except:
        banned_ips = "unbekannt / nicht verfügbar"
        has_banned_ips = False

    return render_template('admin/server_status.html',
        disk_total=disk_total, disk_used=disk_used, disk_free=disk_free, disk_percent=disk_percent,
        mem_total=mem_total, mem_used=mem_used, mem_percent=mem_percent,
        cpu_percent=cpu_percent,
        uptime=uptime,
        system_time=system_time,
        timezone=timezone,
        python_version=python_version,
        flask_version=flask_version,
        banned_ips=banned_ips,
        has_banned_ips=has_banned_ips
    )

@admin_bp.route('/admin/status/live')
@admin_required
def live_status():
    import psutil
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.5)

    return {
        'cpu_percent': cpu,
        'mem_percent': mem.percent,
        'mem_used': round(mem.used / (1024 ** 3), 1)
    }

@admin_bp.route('/admin/status/disk-usage')
@admin_required
def disk_usage():
    import subprocess

    try:
        result = subprocess.run(
            ['du', '-h', '--max-depth=2', '/'],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # unterdrückt die Fehlermeldungen
            timeout=5
        )
        return {'output': result.stdout}
    except Exception as e:
        return {'error': str(e)}, 500


