import os
from flask import Blueprint, render_template, request, flash, abort
from flask_login import current_user
from app.utils import user_has_role

importer_bp = Blueprint('importer', __name__)

@importer_bp.before_request
def check_roles():
    if not any(user_has_role(r) for r in ('Superuser', 'Buchhaltung', 'Management')):
        abort(403)

@importer_bp.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("Keine Datei ausgewählt.", "warning")
        else:
            flash(f"Datei '{file.filename}' empfangen (Platzhalter).", "success")
        return render_template('import/upload.html')
    return render_template('import/upload.html')

@importer_bp.route('/preview')
def preview():
    raws = []  # später: TransactionsRaw.query.order_by(...).all()
    return render_template('import/preview.html', raws=raws)
