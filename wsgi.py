import os
import sys
from dotenv import load_dotenv

# 🐍 Python 3.8+ erforderlich
# 💡 Basisverzeichnis
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 🛠️ .env-Datei liegt außerhalb von app/
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("⚠️ .env nicht gefunden:", dotenv_path)

# Projektpfad hinzufügen
sys.path.insert(0, BASE_DIR)

# App importieren
from app import app as application

