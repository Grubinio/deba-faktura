import os
import logging
from flask import Flask, g
from flask_wtf.csrf import CSRFProtect

# App-Initialisierung
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback123")

# CSRF-Schutz aktivieren
csrf = CSRFProtect(app)

# Logging konfigurieren
log_path = '/var/log/faktura/faktura_app.log'  # Oder relativer Pfad z. B. ../error.log für lokale Entwicklung
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# Session-Sicherheit
# Achtung: SESSION_COOKIE_SECURE nur aktivieren, wenn HTTPS aktiv ist!
# app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Filter einbinden
from .filters import format_currency
app.jinja_env.filters['currency'] = format_currency

# Routen einbinden
from app import routes

# Debug-Modus (nur bei Entwicklung!)
app.debug = True
