# app/importer.py
from flask import (
    Blueprint, render_template, request, flash, abort
)
from app.utils import user_has_role

importer_bp = Blueprint('importer', __name__)

@importer_bp.before_request
def check_roles():
    if not any(user_has_role(r) for r in ('Superuser','Buchhaltung','Management')):
        abort(403)

@importer_bp.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("Keine Datei ausgewählt.", "warning")
        else:
            flash(f"Empfangen: {file.filename}", "success")
        return render_template('import/upload.html')
    return render_template('import/upload.html')

@importer_bp.route('/preview')
def preview():
    raws = []  # später: TransactionsRaw.query...
    return render_template('import/preview.html', raws=raws)
