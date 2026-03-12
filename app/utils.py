from functools import wraps
from flask import session, redirect, url_for, flash
from app.db_pool import get_db_connection
import logging


def user_has_role(role_name):
    if 'user_id' not in session:
        return False

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM user_roles ur
            JOIN rollen r ON ur.rollen_id = r.id
            WHERE ur.user_id = %s AND r.bezeichnung = %s
            LIMIT 1
        """, (session['user_id'], role_name))

        result = cursor.fetchone()
        return result is not None
    except Exception:
        # Niemals im Template-Kontext explodieren lassen (base.html ruft das mehrfach auf).
        logging.exception("Rollenprüfung fehlgeschlagen (role=%s, user_id=%s)", role_name, session.get('user_id'))
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Bitte zuerst einloggen.", "warning")
            return redirect(url_for('auth.login'))

        # Rollenprüfung via Hilfsfunktion
        if not user_has_role('Admin'):
            flash("Zugriff verweigert – Administratorrechte erforderlich.", "danger")
            return redirect(url_for('home'))

        return f(*args, **kwargs)
    return decorated_function
