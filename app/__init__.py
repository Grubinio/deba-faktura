#from app.routes import app

from flask import Flask
app = Flask(__name__)
app.secret_key = 'dein_sicherer_key'

from app import routes
