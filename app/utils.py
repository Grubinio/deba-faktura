from flask import session
from app.db import get_db_connection

def user_has_role(role_name):
    if 'user_id' not in session:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM user_roles ur
        JOIN rollen r ON ur.rollen_id = r.id
        WHERE ur.user_id = %s AND r.bezeichnung = %s
        LIMIT 1
    """, (session['user_id'], role_name))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result is not None
