from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, SelectField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Anmelden')

class RegisterForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    email = EmailField('E-Mail', validators=[DataRequired()])
    funktion = SelectField('Funktion', choices=[
        ('Vertrieb', 'Vertrieb'),
        ('Auftragsabwicklung', 'Auftragsabwicklung'),
        ('Debitorenbuchhaltung', 'Debitorenbuchhaltung'),
        ('Management', 'Management')
    ], validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Benutzer anlegen')

class DeleteUserForm(FlaskForm):
    submit = SubmitField('Löschen')
