import os
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv


print("🚀 Flask-App wird geladen (INIT)")

# 📌 .env laden
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

from config import Config

# Temporär zum Debuggen – kann später raus
print("🚀 DB_HOST aus .env:", os.getenv("DB_HOST"))

# 🔧 App-Initialisierung
app = Flask(__name__)
app.config.from_object(Config)

# 🔒 CSRF-Schutz
csrf = CSRFProtect(app)

# 🧾 Logging
log_path = '/var/log/faktura/faktura_app.log' if not app.debug else os.path.join(os.path.dirname(__file__), '../error.log')
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# 🧠 Eigene Jinja-Filter
from .filters import format_currency, format_datum
app.jinja_env.filters['currency'] = format_currency
app.jinja_env.filters['datum_de'] = format_datum

# 📌 Blueprint-Registrierung
from app.auth import auth_bp
from app.buergschaften import buergschaften_bp
from app.admin import admin_bp
from app.auftraege import bp as auftraege_bp
app.register_blueprint(auftraege_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(buergschaften_bp)

# 🧭 Weitere Module (z. B. routes) importieren
from app import routes  # routes.py bleibt (noch) ohne Blueprint
# Später: app.register_blueprint(main_bp) usw.

# 📅 Kontext für Footer
@app.context_processor
def inject_year():
    from datetime import datetime
    return {'current_year': datetime.now().year}

from app.utils import user_has_role

@app.context_processor
def inject_user_role_check():
    return dict(user_has_role=user_has_role)