import os


def _mysql_sqlalchemy_uri():
    """
    Baut eine robuste SQLAlchemy-URI mit verfügbarem MySQL-Treiber.
    Hintergrund: In Produktion führt ein fehlendes `pymysql` beim App-Import
    schnell zu einem generischen Apache-500.
    """
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'faktura_user')
    password = os.getenv('DB_PASSWORD', 'meinpasswort')
    db_name = os.getenv('DB_NAME', 'faktura_app')

    # Bevorzugt bestehenden Default (pymysql), fällt aber automatisch auf
    # mysql-connector zurück, das im Projekt ebenfalls genutzt wird.
    try:
        import pymysql  # noqa: F401
        driver = 'mysql+pymysql'
    except ModuleNotFoundError:
        driver = 'mysql+mysqlconnector'

    return f"{driver}://{user}:{password}@{host}/{db_name}"

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback123')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    PROPAGATE_EXCEPTIONS = True

    # Beispiel für DB-Zugriff (wenn du willst)
    DB_HOST = os.getenv('DB_HOST', 'localhost')     
    DB_USER = os.getenv('DB_USER', 'faktura_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'meinpasswort')  
    DB_NAME = os.getenv('DB_NAME', 'faktura_app')
    #neu
    DB_POOL_NAME = os.getenv("DB_POOL_NAME", "mypool")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
    
    # → SQLAlchemy-URI aus deinen DB-Variablen zusammenbauen
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', _mysql_sqlalchemy_uri())
    # → Deaktiviert den Change-Tracker (sorgt für weniger Overhead)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
