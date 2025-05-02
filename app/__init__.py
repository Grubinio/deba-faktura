import os
import logging
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
#from app.models import load_user  # falls du `load_user()` separat definiert hast

# 📌 .env laden
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

from config import Config

# 🔧 App-Initialisierung
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # oder dein Login-Endpunkt
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return load_user(user_id)  # oder dein konkreter Ladecode

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
from app.auftraege_routes import bp as auftraege_bp
app.register_blueprint(auftraege_bp)
from app.auth import auth_bp
app.register_blueprint(auth_bp)
from app.admin import admin_bp
app.register_blueprint(admin_bp)
from app.buergschaften import buergschaften_bp
app.register_blueprint(buergschaften_bp)
from app.importer import importer_bp
app.register_blueprint(importer_bp, url_prefix='/import')


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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    import traceback
    tb = traceback.format_exc()
    return f"<h1>Fehler 500</h1><p>{e}</p><pre>{tb}</pre>", 500
