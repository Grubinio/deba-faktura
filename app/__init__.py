import os
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from config import Config

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# App-Initialisierung
app = Flask(__name__)
app.config.from_object(Config)  # ← Lädt zentral alle Settings

# CSRF-Schutz aktivieren
csrf = CSRFProtect(app)

# Logging konfigurieren
log_path = '/var/log/faktura/faktura_app.log' if not app.debug else os.path.join(os.path.dirname(__file__), '../error.log')
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# Eigene Jinja2-Filter einbinden
from .filters import format_currency
app.jinja_env.filters['currency'] = format_currency

# Routes einbinden (ganz am Ende, da sie app brauchen)
from app import routes
