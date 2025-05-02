# app/importer.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user

importer_bp = Blueprint(
    'importer',
    __name__,
    template_folder='templates/import'
)

@importer_bp.before_request
def check_roles():
    # Nur Superuser, Buchhaltung, Management
    from app.utils import user_has_role
    if not any(user_has_role(r) for r in ('Superuser','Buchhaltung','Management')):
        from flask import abort
        abort(403)

@importer_bp.route('/', methods=['GET'])
def upload():
    # Erstmal nur eine Bestätigung, dass das Blueprint lädt
    return render_template('import/upload.html')

@importer_bp.route('/preview', methods=['GET'])
def preview():
    # Platzhalter-Vorschau
    return render_template('import/preview.html', rows=[])
