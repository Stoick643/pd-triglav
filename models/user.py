from datetime import datetime
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Create db instance that will be initialized by app
db = SQLAlchemy()


class UserRole(Enum):
    """User role enumeration"""
    PENDING = 'pending'
    MEMBER = 'member'
    TRIP_LEADER = 'trip_leader'
    ADMIN = 'admin'
    
    @classmethod
    def choices(cls):
        """Return choices for WTForms SelectField"""
        return [(choice.value, choice.value.replace('_', ' ').title()) for choice in cls]


class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic user information
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))
    name = db.Column(db.String(100), nullable=False)
    
    # Role and approval status
    role = db.Column(db.Enum(UserRole), default=UserRole.PENDING, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    
    # OAuth integration
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # User profile (optional fields)
    phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(200))
    bio = db.Column(db.Text)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_pending(self):
        """Check if user is pending approval"""
        return self.role == UserRole.PENDING or not self.is_approved
    
    def is_member(self):
        """Check if user is an approved member"""
        return self.is_approved and self.role in [UserRole.MEMBER, UserRole.TRIP_LEADER, UserRole.ADMIN]
    
    def is_trip_leader(self):
        """Check if user can create and manage trips"""
        return self.is_approved and self.role in [UserRole.TRIP_LEADER, UserRole.ADMIN]
    
    def is_admin(self):
        """Check if user has admin privileges"""
        return self.is_approved and self.role == UserRole.ADMIN
    
    def can_access_content(self):
        """Check if user can access member content"""
        return self.is_member()
    
    def approve(self, role=UserRole.MEMBER):
        """Approve user with specified role"""
        self.is_approved = True
        if role != UserRole.PENDING:
            self.role = role
    
    def reject(self):
        """Reject user approval"""
        self.is_approved = False
        self.role = UserRole.PENDING
    
    def promote_to_trip_leader(self):
        """Promote user to trip leader"""
        if self.is_approved:
            self.role = UserRole.TRIP_LEADER
    
    def promote_to_admin(self):
        """Promote user to admin"""
        if self.is_approved:
            self.role = UserRole.ADMIN
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def create_user(email, name, password=None, google_id=None, role=UserRole.PENDING):
        """Create a new user with proper validation"""
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return None
        
        # Create new user
        user = User(
            email=email,
            name=name,
            role=role,
            google_id=google_id,
            is_approved=False
        )
        
        # Set password if provided (for classical registration)
        if password:
            user.set_password(password)
        
        return user
    
    @staticmethod
    def get_by_email(email):
        """Get user by email address"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_by_google_id(google_id):
        """Get user by Google OAuth ID"""
        return User.query.filter_by(google_id=google_id).first()
    
    @staticmethod
    def get_pending_users():
        """Get all users pending approval"""
        return User.query.filter_by(role=UserRole.PENDING).all()
    
    @staticmethod
    def get_approved_users():
        """Get all approved users"""
        return User.query.filter_by(is_approved=True).all()
    
    @staticmethod
    def get_admins():
        """Get all admin users"""
        return User.query.filter_by(role=UserRole.ADMIN, is_approved=True).all()
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role.value,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }