import sys
from dotenv import load_dotenv
import os

# .env manuell laden – wichtig für Apache/mod_wsgi!
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Projektpfad eintragen
sys.path.insert(0, os.path.dirname(__file__))

##Für Umgebungsvariablen
# Hier wird der Pfad zur .env-Datei gesetzt
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Sicherstellen, dass das Projektverzeichnis im Python-Pfad liegt
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application

# Optional (nur für Entwicklung oder Debug-Zwecke – am besten auslassen in Produktion)
# application.config['DEBUG'] = True
# application.config['PROPAGATE_EXCEPTIONS'] = True
