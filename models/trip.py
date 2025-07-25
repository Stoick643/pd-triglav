from datetime import datetime
from enum import Enum
from models.user import db, User


class TripDifficulty(Enum):
    """Trip difficulty levels for mountaineering"""
    EASY = 'easy'           # Lahka tura
    MODERATE = 'moderate'   # Srednje zahtevna
    DIFFICULT = 'difficult' # Zahtevna
    EXPERT = 'expert'       # Zelo zahtevna
    
    @classmethod
    def choices(cls):
        """Return choices for WTForms SelectField"""
        return [(choice.value, choice.value.title()) for choice in cls]
    
    @property
    def slovenian_name(self):
        """Return Slovenian difficulty names"""
        names = {
            'easy': 'Lahka tura',
            'moderate': 'Srednje zahtevna',
            'difficult': 'Zahtevna',
            'expert': 'Zelo zahtevna'
        }
        return names.get(self.value, self.value)


class TripStatus(Enum):
    """Trip status enumeration"""
    ANNOUNCED = 'announced'   # Objavljena
    CANCELLED = 'cancelled'   # Odpovedana
    COMPLETED = 'completed'   # Opravljena
    
    @classmethod
    def choices(cls):
        """Return choices for WTForms SelectField"""
        return [(choice.value, choice.value.title()) for choice in cls]


class Trip(db.Model):
    """Trip model for mountaineering excursions"""
    
    __tablename__ = 'trips'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic trip information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    destination = db.Column(db.String(200), nullable=False)
    
    # Trip scheduling
    trip_date = db.Column(db.Date, nullable=False)
    meeting_time = db.Column(db.Time)
    meeting_point = db.Column(db.String(200))
    return_time = db.Column(db.Time)
    
    # Trip details
    difficulty = db.Column(db.Enum(TripDifficulty), nullable=False, default=TripDifficulty.MODERATE)
    max_participants = db.Column(db.Integer)  # None = unlimited
    equipment_needed = db.Column(db.Text)
    cost_per_person = db.Column(db.Float)  # Cost in euros
    
    # Trip management
    status = db.Column(db.Enum(TripStatus), nullable=False, default=TripStatus.ANNOUNCED)
    
    # Foreign keys
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    leader = db.relationship('User', backref='led_trips', lazy=True)
    participants = db.relationship('TripParticipant', backref='trip', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('TripReport', backref='trip', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Trip {self.title} - {self.trip_date}>'
    
    @property
    def is_full(self):
        """Check if trip has reached maximum participants"""
        if not self.max_participants:
            return False
        confirmed_count = len([p for p in self.participants if p.status == ParticipantStatus.CONFIRMED])
        return confirmed_count >= self.max_participants
    
    @property
    def confirmed_participants_count(self):
        """Get count of confirmed participants"""
        return len([p for p in self.participants if p.status == ParticipantStatus.CONFIRMED])
    
    @property
    def waitlist_count(self):
        """Get count of waitlisted participants"""
        return len([p for p in self.participants if p.status == ParticipantStatus.WAITLISTED])
    
    @property
    def is_past(self):
        """Check if trip date has passed"""
        from datetime import date
        return self.trip_date < date.today()
    
    @property
    def can_signup(self):
        """Check if users can still sign up for this trip"""
        return (self.status == TripStatus.ANNOUNCED and 
                not self.is_past)
    
    def get_participant_status(self, user):
        """Get user's participation status for this trip"""
        participant = TripParticipant.query.filter_by(
            trip_id=self.id, 
            user_id=user.id
        ).first()
        return participant.status if participant else None
    
    def can_user_signup(self, user):
        """Check if user can sign up for this trip"""
        if not self.can_signup:
            return False
        
        # Check if user is already signed up
        existing_participant = TripParticipant.query.filter_by(
            trip_id=self.id,
            user_id=user.id
        ).first()
        
        return existing_participant is None
    
    def add_participant(self, user):
        """Add user as participant (confirmed or waitlisted)"""
        if not self.can_user_signup(user):
            return None
        
        # Determine status based on capacity
        if self.is_full:
            status = ParticipantStatus.WAITLISTED
        else:
            status = ParticipantStatus.CONFIRMED
        
        participant = TripParticipant(
            trip_id=self.id,
            user_id=user.id,
            status=status
        )
        
        db.session.add(participant)
        return participant
    
    def remove_participant(self, user):
        """Remove user from trip and promote waitlisted users"""
        participant = TripParticipant.query.filter_by(
            trip_id=self.id,
            user_id=user.id
        ).first()
        
        if not participant:
            return False
        
        was_confirmed = participant.status == ParticipantStatus.CONFIRMED
        db.session.delete(participant)
        
        # If confirmed participant left, promote first waitlisted
        if was_confirmed:
            waitlisted = TripParticipant.query.filter_by(
                trip_id=self.id,
                status=ParticipantStatus.WAITLISTED
            ).order_by(TripParticipant.signup_date).first()
            
            if waitlisted:
                waitlisted.status = ParticipantStatus.CONFIRMED
        
        return True
    
    @staticmethod
    def get_upcoming_trips():
        """Get all upcoming announced trips"""
        from datetime import date
        return Trip.query.filter(
            Trip.trip_date >= date.today(),
            Trip.status == TripStatus.ANNOUNCED
        ).order_by(Trip.trip_date).all()
    
    @staticmethod
    def get_past_trips():
        """Get all past trips"""
        from datetime import date
        return Trip.query.filter(
            Trip.trip_date < date.today()
        ).order_by(Trip.trip_date.desc()).all()
    
    @staticmethod
    def get_trips_by_leader(leader_id):
        """Get all trips led by specific user"""
        return Trip.query.filter_by(leader_id=leader_id).order_by(Trip.trip_date.desc()).all()
    
    def to_dict(self):
        """Convert trip to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'destination': self.destination,
            'trip_date': self.trip_date.isoformat() if self.trip_date else None,
            'difficulty': self.difficulty.value,
            'difficulty_name': self.difficulty.slovenian_name,
            'leader': self.leader.name,
            'confirmed_participants': self.confirmed_participants_count,
            'waitlist_count': self.waitlist_count,
            'status': self.status.value,
            'can_signup': self.can_signup
        }


class ParticipantStatus(Enum):
    """Participant status enumeration"""
    CONFIRMED = 'confirmed'     # Potrjen
    WAITLISTED = 'waitlisted'   # Na čakalni listi
    CANCELLED = 'cancelled'     # Odpovedal
    
    @classmethod
    def choices(cls):
        """Return choices for WTForms SelectField"""
        return [(choice.value, choice.value.title()) for choice in cls]


class TripParticipant(db.Model):
    """Trip participant model (many-to-many relationship)"""
    
    __tablename__ = 'trip_participants'
    
    # Composite primary key
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Participant details
    status = db.Column(db.Enum(ParticipantStatus), nullable=False, default=ParticipantStatus.CONFIRMED)
    signup_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)  # Special requirements, emergency contact, etc.
    
    # Relationships
    user = db.relationship('User', backref='trip_participations', lazy=True)
    
    def __repr__(self):
        return f'<TripParticipant {self.user.name} - {self.trip.title}>'
    
    def promote_from_waitlist(self):
        """Promote participant from waitlist to confirmed"""
        if self.status == ParticipantStatus.WAITLISTED:
            self.status = ParticipantStatus.CONFIRMED
            return True
        return False
    
    def cancel_participation(self):
        """Cancel user's participation"""
        self.status = ParticipantStatus.CANCELLED
    
    @staticmethod
    def get_user_trips(user_id, status=None):
        """Get all trips for a user, optionally filtered by status"""
        query = TripParticipant.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.all()
    
    def to_dict(self):
        """Convert participant to dictionary for JSON serialization"""
        return {
            'user_id': self.user_id,
            'user_name': self.user.name,
            'status': self.status.value,
            'signup_date': self.signup_date.isoformat() if self.signup_date else None,
            'notes': self.notes
        }