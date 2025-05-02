#!/usr/bin/env python3
# /var/www/faktura/scripts.py

import os
import pandas as pd
from wsgi import application
from app import db
from app.models import CategoriesTransaction

def seed_categories():
    # 1) Finde die Excel-Datei unter Temp/Kategorien.xlsx
    base_dir    = os.path.abspath(os.path.dirname(__file__))
    excel_path  = os.path.join(base_dir, 'Temp', 'Kategorien.xlsx')
    if not os.path.exists(excel_path):
        print(f"❌ Excel-Datei nicht gefunden: {excel_path}")
        return

    # 2) Sheet einlesen (Sheet 0, oder gib hier den Namen an)
    df = pd.read_excel(
        excel_path,
        sheet_name=0,     # ggf. Name: sheet_name="DeinSheet"
        engine='openpyxl'
    )

    # 3) Spalten prüfen
    # Erwarte df.columns enthält mindestens 'Buchungstext' und 'Kategorie'
    print("Spalten in Excel:", df.columns.tolist())

    with application.app_context():
        # 4) Alte Kategorien löschen (optional)
        deleted = db.session.query(CategoriesTransaction).delete()
        print(f"ℹ️ {deleted} alte Kategorien gelöscht")

        # 5) Neue anlegen
        added = 0
        for _, row in df.iterrows():
            name = str(row.get('Kategorie','')).strip()
            if name:
                cat = CategoriesTransaction(name=name)
                db.session.add(cat)
                added += 1

        db.session.commit()
        total = db.session.query(CategoriesTransaction).count()
        print(f"✅ {added} Kategorien importiert (insgesamt jetzt {total})")

if __name__ == '__main__':
    seed_categories()
