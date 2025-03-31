#from app.routes import app

from flask import Flask
from flask import g

app = Flask(__name__)
app.secret_key = 'dein_sicherer_key'

from app import routes

app.debug = True

from .filters import format_currency
app.jinja_env.filters['currency'] = format_currency
