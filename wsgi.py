import sys
import os

# Sicherstellen, dass das Projektverzeichnis im Python-Pfad liegt
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application

# Optional (nur für Entwicklung oder Debug-Zwecke – am besten auslassen in Produktion)
# application.config['DEBUG'] = True
# application.config['PROPAGATE_EXCEPTIONS'] = True
