"""Authentication forms for PD Triglav application"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from wtforms.widgets import TextInput, PasswordInput
from models.user import User
import re


class LoginForm(FlaskForm):
    """User login form"""
    email = StringField('Email', validators=[
        DataRequired(message='Email je obvezen.'),
        Email(message='Vnesite veljaven email naslov.')
    ], render_kw={'placeholder': 'vas@email.com'})
    
    password = PasswordField('Geslo', validators=[
        DataRequired(message='Geslo je obvezno.')
    ], render_kw={'placeholder': 'Vaše geslo'})
    
    remember = BooleanField('Zapomni si me')
    submit = SubmitField('Prijava')


class RegistrationForm(FlaskForm):
    """User registration form"""
    name = StringField('Ime in priimek', validators=[
        DataRequired(message='Ime in priimek sta obvezna.'),
        Length(min=2, max=100, message='Ime mora imeti med 2 in 100 znakov.')
    ], render_kw={'placeholder': 'Janez Novak'})
    
    email = StringField('Email', validators=[
        DataRequired(message='Email je obvezen.'),
        Email(message='Vnesite veljaven email naslov.'),
        Length(max=120, message='Email naslov je predolg.')
    ], render_kw={'placeholder': 'janez@email.com'})
    
    password = PasswordField('Geslo', validators=[
        DataRequired(message='Geslo je obvezno.'),
        Length(min=8, message='Geslo mora imeti vsaj 8 znakov.')
    ], render_kw={'placeholder': 'Najmanj 8 znakov'})
    
    password_confirm = PasswordField('Ponovite geslo', validators=[
        DataRequired(message='Potrdite geslo.'),
        EqualTo('password', message='Gesli se ne ujemata.')
    ], render_kw={'placeholder': 'Ponovite geslo'})
    
    submit = SubmitField('Registracija')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.get_by_email(email.data)
        if user:
            raise ValidationError('Ta email naslov je že registriran.')
    
    def validate_password(self, password):
        """Validate password strength"""
        pwd = password.data
        
        # Check for minimum complexity
        if len(pwd) < 8:
            raise ValidationError('Geslo mora imeti vsaj 8 znakov.')
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', pwd):
            raise ValidationError('Geslo mora vsebovati vsaj eno črko.')
        
        if not re.search(r'\d', pwd):
            raise ValidationError('Geslo mora vsebovati vsaj eno številko.')
        
        # Check for common weak passwords
        weak_passwords = [
            'password', 'geslo', '12345678', 'qwerty123', 
            'password123', 'geslo123', 'admin123'
        ]
        if pwd.lower() in weak_passwords:
            raise ValidationError('Geslo je preveč pogosto. Izberite drugačno geslo.')
    
    def validate_name(self, name):
        """Validate name for XSS and basic sanitization"""
        if '<' in name.data or '>' in name.data:
            raise ValidationError('Ime ne sme vsebovati HTML značk.')
        
        if 'script' in name.data.lower():
            raise ValidationError('Ime vsebuje prepovedano vsebino.')


class PasswordResetRequestForm(FlaskForm):
    """Password reset request form"""
    email = StringField('Email', validators=[
        DataRequired(message='Email je obvezen.'),
        Email(message='Vnesite veljaven email naslov.')
    ], render_kw={'placeholder': 'vas@email.com'})
    
    submit = SubmitField('Pošlji zahtevo za ponastavitev')


class PasswordResetForm(FlaskForm):
    """Password reset form"""
    password = PasswordField('Novo geslo', validators=[
        DataRequired(message='Geslo je obvezno.'),
        Length(min=8, message='Geslo mora imeti vsaj 8 znakov.')
    ], render_kw={'placeholder': 'Najmanj 8 znakov'})
    
    password_confirm = PasswordField('Ponovite novo geslo', validators=[
        DataRequired(message='Potrdite geslo.'),
        EqualTo('password', message='Gesli se ne ujemata.')
    ], render_kw={'placeholder': 'Ponovite novo geslo'})
    
    submit = SubmitField('Ponastavi geslo')
    
    def validate_password(self, password):
        """Validate password strength"""
        pwd = password.data
        
        # Check for minimum complexity
        if len(pwd) < 8:
            raise ValidationError('Geslo mora imeti vsaj 8 znakov.')
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', pwd):
            raise ValidationError('Geslo mora vsebovati vsaj eno črko.')
        
        if not re.search(r'\d', pwd):
            raise ValidationError('Geslo mora vsebovati vsaj eno številko.')
        
        # Check for common weak passwords
        weak_passwords = [
            'password', 'geslo', '12345678', 'qwerty123', 
            'password123', 'geslo123', 'admin123'
        ]
        if pwd.lower() in weak_passwords:
            raise ValidationError('Geslo je preveč pogosto. Izberite drugačno geslo.')


class ChangePasswordForm(FlaskForm):
    """Change password form for logged-in users"""
    current_password = PasswordField('Trenutno geslo', validators=[
        DataRequired(message='Trenutno geslo je obvezno.')
    ], render_kw={'placeholder': 'Vnesite trenutno geslo'})
    
    new_password = PasswordField('Novo geslo', validators=[
        DataRequired(message='Novo geslo je obvezno.'),
        Length(min=8, message='Geslo mora imeti vsaj 8 znakov.')
    ], render_kw={'placeholder': 'Najmanj 8 znakov'})
    
    new_password_confirm = PasswordField('Ponovite novo geslo', validators=[
        DataRequired(message='Potrdite novo geslo.'),
        EqualTo('new_password', message='Gesli se ne ujemata.')
    ], render_kw={'placeholder': 'Ponovite novo geslo'})
    
    submit = SubmitField('Spremeni geslo')
    
    def validate_new_password(self, new_password):
        """Validate new password strength"""
        pwd = new_password.data
        
        # Check for minimum complexity
        if len(pwd) < 8:
            raise ValidationError('Geslo mora imeti vsaj 8 znakov.')
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', pwd):
            raise ValidationError('Geslo mora vsebovati vsaj eno črko.')
        
        if not re.search(r'\d', pwd):
            raise ValidationError('Geslo mora vsebovati vsaj eno številko.')
        
        # Check for common weak passwords
        weak_passwords = [
            'password', 'geslo', '12345678', 'qwerty123', 
            'password123', 'geslo123', 'admin123'
        ]
        if pwd.lower() in weak_passwords:
            raise ValidationError('Geslo je preveč pogosto. Izberite drugačno geslo.')