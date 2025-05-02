import os
import logging
from flask import (
    Blueprint, render_template, request,
    flash, redirect, url_for, abort
)
from werkzeug.utils import secure_filename
import pandas as pd

from app import db
from app.models import TransactionsRaw, CategoriesTransaction
from app.utils import user_has_role

# Blueprint wie gehabt
importer_bp = Blueprint('importer', __name__)

# Ordner für temporäre Uploads (Projekt-Root/uploads_temp)
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'uploads_temp')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@importer_bp.before_request
def check_roles():
    if not any(user_has_role(r) for r in ('Superuser','Buchhaltung','Management')):
        abort(403)

@importer_bp.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash("Bitte eine XLSX- oder CSV-Datei auswählen.", "warning")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            # 1) Datei speichern
            file.save(filepath)
            logging.info(f"Importer: Datei gespeichert: {filepath}")

            # 2) DataFrame einlesen
            if filename.lower().endswith(('.xls', '.xlsx')):
                xls = pd.ExcelFile(filepath, engine='openpyxl')
                target_sheet = 'IST-Zahlungsdaten'
                if target_sheet in xls.sheet_names:
                    df = xls.parse(target_sheet)
                else:
                    # Fallback: erstes Sheet
                    df = xls.parse(xls.sheet_names[0])
            else:
                df = pd.read_csv(filepath)


            # 3) Spalten umbenennen
            df = df.rename(columns={
                'Auftraggeber': 'auftraggeber',
                'Art': 'art',
                'Kontoname': 'kontoname',
                'Buchungstext': 'buchungstext',
                'Begünstigter/Zahlungspflichtiger': 'beguenstigter',
                'Verwendungszweck': 'verwendungszweck',
                'Buchung': 'buchung',
                'Wertstellung': 'wertstellung',
                'Betrag': 'betrag',
                'Währung': 'waehrung',
                'Auszugsnr.': 'auszugsnr',
                'Original-Währung': 'original_waehrung',
            })
            # ersetze alle numpy.nan und pandas.NaT durch None
            df = df.where(pd.notnull(df), None)


            # 4) Objekte erzeugen
            raws = []
            for idx, row in df.iterrows():
                raws.append(TransactionsRaw(
                    auftraggeber      = row.get('auftraggeber'),
                    art               = row.get('art'),
                    kontoname         = row.get('kontoname'),
                    buchungstext      = row.get('buchungstext'),
                    beguenstigter     = row.get('beguenstigter'),
                    verwendungszweck  = row.get('verwendungszweck'),
                    buchung           = row.get('buchung'),
                    wertstellung      = row.get('wertstellung'),
                    betrag            = row.get('betrag'),
                    waehrung          = row.get('waehrung'),
                    auszugsnr         = row.get('auszugsnr'),
                    original_waehrung = row.get('original_waehrung'),
                ))
            db.session.bulk_save_objects(raws)
            db.session.commit()
            flash(f"{len(raws)} Zeilen erfolgreich importiert.", "success")
            logging.info(f"Importer: {len(raws)} Zeilen importiert aus {filename}")

            return redirect(url_for('importer.preview'))

        except Exception as e:
            db.session.rollback()
            logging.exception("Importer-Fehler beim Einlesen")
            # Zeige das Exception-Message direkt im Flash
            flash(f"Fehler beim Import: {e}", "danger")
            return redirect(request.url)

        finally:
            # 5) Temp-Datei löschen
            try:
                os.remove(filepath)
            except OSError:
                pass

    return render_template('import/upload.html')

@importer_bp.route('/preview')
def preview():
    from app.models import TransactionsRaw
    # Letzte 100 Roh-Einträge holen, absteigend nach Import-Datum
    raws = (
        TransactionsRaw.query
        .order_by(TransactionsRaw.import_date.desc())
        .limit(100)
        .all()
    )
    return render_template('import/preview.html', raws=raws)
