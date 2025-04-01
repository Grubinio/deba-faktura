import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback123')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    PROPAGATE_EXCEPTIONS = True

    # Beispiel für DB-Zugriff (wenn du willst)
    DB_USER = os.getenv('DB_USER', 'faktura_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'meinpasswort')
    DB_NAME = os.getenv('DB_NAME', 'faktura_app')