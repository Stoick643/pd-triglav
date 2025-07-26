"""Forms for trip management"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, MultipleFileField, FileAllowed, FileSize
from wtforms import StringField, TextAreaField, DateField, TimeField, SelectField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from datetime import date, timedelta
from models.trip import TripDifficulty, TripStatus


def coerce_int_or_none(value):
    """Coerce to int, but return None for empty strings"""
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class TripForm(FlaskForm):
    """Form for creating and editing trip announcements"""
    
    # Basic trip information
    title = StringField('Naslov izleta', validators=[
        DataRequired(message='Naslov je obvezen.'),
        Length(min=5, max=200, message='Naslov mora biti dolg med 5 in 200 znakov.')
    ])
    
    description = TextAreaField('Opis izleta', validators=[
        Optional(),
        Length(max=2000, message='Opis ne sme biti daljši od 2000 znakov.')
    ])
    
    destination = StringField('Cilj/destinacija', validators=[
        DataRequired(message='Cilj je obvezen.'),
        Length(min=2, max=200, message='Cilj mora biti dolg med 2 in 200 znakov.')
    ])
    
    # Trip scheduling
    trip_date = DateField('Datum izleta', validators=[
        DataRequired(message='Datum izleta je obvezen.')
    ])
    
    meeting_time = TimeField('Čas zbiranja', validators=[Optional()])
    
    meeting_point = StringField('Mesto zbiranja', validators=[
        Optional(),
        Length(max=200, message='Mesto zbiranja ne sme biti daljše od 200 znakov.')
    ])
    
    return_time = TimeField('Predviden čas vrnitve', validators=[Optional()])
    
    # Trip details
    difficulty = SelectField('Zahtevnost', validators=[
        DataRequired(message='Zahtevnost je obvezna.')
    ], choices=[
        (TripDifficulty.EASY.value, 'Lahka tura'),
        (TripDifficulty.MODERATE.value, 'Srednje zahtevna'),
        (TripDifficulty.DIFFICULT.value, 'Zahtevna'),
        (TripDifficulty.EXPERT.value, 'Zelo zahtevna')
    ])
    
    max_participants = IntegerField('Največ udeležencev', validators=[
        Optional(),
        NumberRange(min=1, max=100, message='Število udeležencev mora biti med 1 in 100.')
    ])
    
    equipment_needed = TextAreaField('Potrebna oprema', validators=[
        Optional(),
        Length(max=1000, message='Opis opreme ne sme biti daljši od 1000 znakov.')
    ])
    
    cost_per_person = FloatField('Cena na osebo (€)', validators=[
        Optional(),
        NumberRange(min=0, max=1000, message='Cena mora biti med 0 in 1000 €.')
    ])
    
    # Submit buttons
    submit = SubmitField('Objavi izlet')
    save_draft = SubmitField('Shrani osnutek')
    
    def validate_trip_date(self, field):
        """Custom validation for trip date"""
        if field.data and field.data < date.today():
            raise ValidationError('Datum izleta ne more biti v preteklosti.')
        
        # Reasonable future limit (2 years)
        max_date = date.today() + timedelta(days=730)
        if field.data and field.data > max_date:
            raise ValidationError('Datum izleta je preveč v prihodnosti.')


class TripSignupForm(FlaskForm):
    """Form for signing up for trips"""
    
    notes = TextAreaField('Opombe (izbirno)', validators=[
        Optional(),
        Length(max=500, message='Opombe ne smejo biti daljše od 500 znakov.')
    ], description='Posebne potrebe, izkušnje, kontakt v sili, itd.')
    
    submit = SubmitField('Prijavi se na izlet')


class TripCommentForm(FlaskForm):
    """Form for adding comments to trip announcements"""
    
    content = TextAreaField('Komentar', validators=[
        DataRequired(message='Komentar ne more biti prazen.'),
        Length(min=1, max=1000, message='Komentar mora biti dolg med 1 in 1000 znakov.')
    ])
    
    submit = SubmitField('Objavi komentar')


class TripFilterForm(FlaskForm):
    """Form for filtering trip listings"""
    
    difficulty = SelectField('Zahtevnost', validators=[Optional()], choices=[
        ('', 'Vse zahtevnosti'),
        (TripDifficulty.EASY.value, 'Lahka tura'),
        (TripDifficulty.MODERATE.value, 'Srednje zahtevna'),
        (TripDifficulty.DIFFICULT.value, 'Zahtevna'),
        (TripDifficulty.EXPERT.value, 'Zelo zahtevna')
    ])
    
    status = SelectField('Status', validators=[Optional()], choices=[
        ('', 'Vsi statusi'),
        ('upcoming', 'Prihajajoči izleti'),
        ('past', 'Pretekli izleti'),
        (TripStatus.ANNOUNCED.value, 'Objavljeni'),
        (TripStatus.COMPLETED.value, 'Opravljeni'),
        (TripStatus.CANCELLED.value, 'Odpovejdani')
    ])
    
    search = StringField('Iskanje', validators=[
        Optional(),
        Length(max=100, message='Iskalni niz ne sme biti daljši od 100 znakov.')
    ], description='Išči po naslovu ali cilju')
    
    submit = SubmitField('Filtriraj')


class TripReportForm(FlaskForm):
    """Form for creating and editing trip reports"""
    
    title = StringField('Naslov poročila', validators=[
        DataRequired(message='Naslov je obvezen.'),
        Length(min=5, max=200, message='Naslov mora biti dolg med 5 in 200 znakov.')
    ])
    
    summary = TextAreaField('Kratek povzetek', validators=[
        Optional(),
        Length(max=500, message='Povzetek ne sme biti daljši od 500 znakov.')
    ], description='Kratek opis izkušnje za seznam poročil')
    
    content = TextAreaField('Vsebina poročila', validators=[
        DataRequired(message='Vsebina poročila je obvezna.'),
        Length(min=50, message='Poročilo mora biti dolgo vsaj 50 znakov.')
    ], description='Podroben opis vaše izkušnje, vtisov, priporočil...')
    
    # Weather and trail conditions
    weather_conditions = StringField('Vremenske razmere', validators=[
        Optional(),
        Length(max=200, message='Opis vremenskih razmer ne sme biti daljši od 200 znakov.')
    ], description='Sončno, oblačno, dež, sneg, temperatura...')
    
    trail_conditions = StringField('Stanje poti', validators=[
        Optional(),
        Length(max=200, message='Opis stanja poti ne sme biti daljši od 200 znakov.')
    ], description='Suho, mokro, zasneženo, potreba po derezah...')
    
    # Photo upload
    photos = MultipleFileField('Fotografije', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], message='Dovoljene so samo slike (JPG, PNG, GIF).'),
        FileSize(max_size=10*1024*1024, message='Velikost slike ne sme presegati 10 MB.')
    ], description='Izberite do 10 fotografij za poročilo (JPG, PNG, GIF, do 10 MB vsaka)')
    
    # Publication settings
    is_published = SelectField('Objavi poročilo', validators=[
        DataRequired()
    ], choices=[
        ('true', 'Da, objavi poročilo'),
        ('false', 'Ne, shrani kot osnutek')
    ], default='true')
    
    submit = SubmitField('Objavi poročilo')
    save_draft = SubmitField('Shrani osnutek')
    
    def validate_photos(self, field):
        """Custom validation for photo uploads"""
        if field.data:
            # Limit number of photos
            if len(field.data) > 10:
                raise ValidationError('Lahko naložite največ 10 fotografij naenkrat.')
            
            # Check if any files are actually uploaded
            uploaded_files = [f for f in field.data if f.filename != '']
            if len(uploaded_files) != len(field.data):
                # Remove empty file entries
                field.data = uploaded_files


class TripReportFilterForm(FlaskForm):
    """Form for filtering trip reports"""
    
    search = StringField('Iskanje', validators=[
        Optional(),
        Length(max=100, message='Iskalni niz ne sme biti daljši od 100 znakov.')
    ], description='Išči po naslovu, povzetku ali avtorju')
    
    trip_id = SelectField('Izlet', validators=[Optional()], choices=[], coerce=coerce_int_or_none)
    
    author = StringField('Avtor', validators=[
        Optional(),
        Length(max=100, message='Ime avtorja ne sme biti daljše od 100 znakov.')
    ])
    
    featured_only = SelectField('Prikaži', validators=[Optional()], choices=[
        ('', 'Vsa poročila'),
        ('featured', 'Samo označena'),
        ('recent', 'Najnovejša')
    ])
    
    submit = SubmitField('Filtriraj')