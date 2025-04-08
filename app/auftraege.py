from flask import Blueprint, render_template, abort, Response
from app.db import get_db_connection

bp = Blueprint('auftraege', __name__, url_prefix='/auftrag')

@bp.route('/<kurznummer>')
def auftrag_detail(kurznummer):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM auftraege WHERE kurznummer = %s", (kurznummer,))
    auftrag = cursor.fetchone()
    cursor.close()
    conn.close()

    if not auftrag:
        abort(404)

    return render_template('auftrag_detail.html', auftrag=auftrag)

@bp.route('/neuer')
def neuer_auftrag():
    return "Neuen Auftrag anlegen (Platzhalter)"

@bp.route('/filter')
def filter_auftraege():
    return "Aufträge filtern (Platzhalter)"
