from app import app

app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

application = app  # <- Apache sucht nach "application"