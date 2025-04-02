import os
import sys
from dotenv import load_dotenv

# 💡 Basisverzeichnis (Projektverzeichnis)
BASE_DIR = os.path.dirname(__file__)

# ✅ .env-Datei laden (sehr früh!)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 🔁 Projektpfad hinzufügen
sys.path.insert(0, BASE_DIR)

# ✅ Flask-App importieren
from app import app as application
