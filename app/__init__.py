#from app.routes import app

from flask import Flask
from flask import g
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)


app = Flask(__name__)
app.secret_key = 'dein_sicherer_key'

import os
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../error.log')
logging.basicConfig(filename='/var/log/faktura_app.log', ...)

from app import routes

app.debug = True

from .filters import format_currency
app.jinja_env.filters['currency'] = format_currency

#app.config['SESSION_COOKIE_SECURE'] = True         # Nur über HTTPS senden (aktivieren, wenn SSL aktiv ist) #💡 Hinweis: SESSION_COOKIE_SECURE wirkt nur bei HTTPS – lokal in Entwicklung kannst du es auf False lassen, auf dem Server auf True stellen.
app.config['SESSION_COOKIE_HTTPONLY'] = True       # Kein JavaScript-Zugriff auf Cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'      # Grundschutz gegen CSRF bei Cross-Site-Requests

