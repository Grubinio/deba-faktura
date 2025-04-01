import os
import sys

# Pfad zur .env-Datei festlegen und laden (ganz am Anfang!)
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Projektverzeichnis zum Python-Pfad hinzufügen
sys.path.insert(0, os.path.dirname(__file__))

# App laden (jetzt greifen os.getenv() korrekt)
from app import app as application
