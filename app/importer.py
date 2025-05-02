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

ALLOWED_EXTENSIONS = {'xlsx', 'csv'}  # .xls fliegt raus

@importer_bp.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("Keine Datei ausgewählt.", "warning")
            return redirect(request.url)

        ext = file.filename.rsplit('.',1)[-1].lower()
        if ext == 'xls':
            flash("Alte .xls-Dateien bitte in .xlsx umwandeln oder als CSV speichern.", "warning")
            return redirect(request.url)
        if ext not in ALLOWED_EXTENSIONS:
            flash("Nur .xlsx und .csv sind erlaubt.", "warning")
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


@importer_bp.route('/preview', methods=['GET','POST'])
def preview():
    # —————————————————————
    # POST: gesendete Kategorien speichern
    if request.method == 'POST':
        for key, val in request.form.items():
            if not key.startswith("category_"):
                continue
            raw_id = int(key.split("_",1)[1])
            # val ist entweder eine Kategorien-ID oder ein Freitext
            if val.isdigit():
                # bestehende Kategorie aus DB
                cat_id = int(val)
            else:
                # neuen Namen anlegen und DB-Id holen
                new_cat = CategoriesTransaction(name=val)
                db.session.add(new_cat)
                db.session.flush()
                cat_id = new_cat.id
            # raw-Eintrag updaten
            raw = TransactionsRaw.query.get(raw_id)
            raw.kategorie_id = cat_id
        db.session.commit()
        flash("✅ Kategorien gespeichert", "success")
        return redirect(request.url)
    # —————————————————————

    # Lade ALLE Roh-Daten
    raws = TransactionsRaw.query.order_by(TransactionsRaw.id).all()
    # Lade alle Kategorien für das Dropdown
    categories = CategoriesTransaction.query.order_by(CategoriesTransaction.name).all()

    # Mapping-Logik (optional) vorbefüllen
    # z.B. aus Excel-Mapping, falls schon implementiert…
    # r.default_kat_id = …

    # Gruppierung nach Konto wie gehabt
    groups = {}
    for r in raws:
        acct = f"{r.kontoname.split(',',1)[1].split()[0]} {r.waehrung}"
        groups.setdefault(acct, []).append(r)

    return render_template(
        'import/preview.html',
        groups=groups,
        categories=categories
    )
