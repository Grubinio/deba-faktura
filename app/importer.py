import os
import logging
from flask import (
    Blueprint, render_template, request,
    flash, redirect, url_for, abort
)
from werkzeug.utils import secure_filename
import pandas as pd
import hashlib  
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

        # 0) Datei speichern wie gehabt
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 1) SHA256-Hash der Datei
        with open(filepath, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # 2) Prüfen, ob der Hash schon da ist
        from app.models import ImportBatch
        if ImportBatch.query.filter_by(file_hash=file_hash).first():
            flash("Diese Datei wurde bereits importiert.", "warning")
            os.remove(filepath)
            return redirect(request.url)

        # 3) Neue Batch anlegen
        batch = ImportBatch(file_hash=file_hash, filename=filename)
        db.session.add(batch)
        db.session.commit()


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
            # ❌ Droppe komplett leere Zeilen
            df = df.dropna(how='all')
            # ✅ Stelle sicher, dass 'buchung' existiert und nicht NaT ist
            if 'buchung' in df.columns:
                df = df[df['buchung'].notna()]
            # ersetze alle numpy.nan und pandas.NaT durch None
            df = df.where(pd.notnull(df), None)


            # 4) Objekte erzeugen
            raws = []
            for _, row in df.iterrows():
                raws.append(TransactionsRaw(
                    auftraggeber      = row['auftraggeber']      if pd.notnull(row['auftraggeber'])      else None,
                    art               = row['art']               if pd.notnull(row['art'])               else None,
                    kontoname         = row['kontoname']         if pd.notnull(row['kontoname'])         else None,
                    buchungstext      = row['buchungstext']      if pd.notnull(row['buchungstext'])      else None,
                    beguenstigter     = row['beguenstigter']     if pd.notnull(row['beguenstigter'])     else None,
                    verwendungszweck  = row['verwendungszweck']  if pd.notnull(row['verwendungszweck'])  else None,
                    # Datumsfelder: NaT → None, ansonsten Datumsteil extrahieren
                    buchung           = (row['buchung'].date() 
                                        if pd.notnull(row['buchung']) else None),
                    wertstellung      = (row['wertstellung'].date() 
                                        if pd.notnull(row['wertstellung']) else None),
                    # Numerisch → None bei nan
                    betrag            = row['betrag']            if pd.notnull(row['betrag'])            else None,
                    waehrung          = row['waehrung']          if pd.notnull(row['waehrung'])          else None,
                    auszugsnr         = row['auszugsnr']         if pd.notnull(row['auszugsnr'])         else None,
                    original_waehrung = row['original_waehrung'] if pd.notnull(row['original_waehrung']) else None,
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
    # hole alle Roh-Daten (ggf. mit Limit und Sort)
    raws = (
        TransactionsRaw.query
        .order_by(TransactionsRaw.import_date.desc())
        .all()
    )

    # gruppiere nach „Bank + Währung“
    groups: dict[str, list[TransactionsRaw]] = {}
    for r in raws:
        # Original-Kontoname aus dem Import, z.B. "EUR 405278169, LBBW/BW-Bank Stuttgart"
        raw_name = r.kontoname or ""
        parts = raw_name.split(',', 1)
        # Teil nach dem Komma (Bank-Teil), falle zurück auf raw_name wenn kein Komma
        bank_part = parts[1].strip() if len(parts) > 1 else raw_name
        # nimm vor dem ersten Leer- oder Slash-Zeichen
        bank = bank_part.split()[0].split('/')[0]
        # einfache Kontobezeichnung
        acct = f"{bank} {r.waehrung}"

        groups.setdefault(acct, []).append(r)

    return render_template('import/preview.html', groups=groups)
