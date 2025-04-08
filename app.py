# app.py
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
	return "Hallo Georg - DEBA Faktura läuft!"