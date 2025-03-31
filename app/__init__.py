#from app.routes import app

from flask import Flask
from flask import g

app = Flask(__name__)
app.secret_key = 'dein_sicherer_key'

from app import routes

@app.context_processor
def inject_user_role_check():
    return dict(user_has_role=user_has_role)

app.debug = True