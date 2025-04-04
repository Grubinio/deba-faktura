import os
import sys
from dotenv import load_dotenv


##temp
import traceback

try:
    print("📦 WSGI wird geladen!")
    sys.stdout = sys.stderr  # Wichtiger Trick für mod_wsgi
except Exception as e:
    print("💥 Fehler beim Start von WSGI:")
    traceback.print_exc()
#Temp ende

print("📦 WSGI wird geladen!")

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

print("✅ App erfolgreich geladen!")