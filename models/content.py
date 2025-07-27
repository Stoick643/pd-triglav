from datetime import datetime
from enum import Enum
from models.user import db, User


class TripReport(db.Model):
    """Trip report model for sharing experiences and photos"""
    
    __tablename__ = 'trip_reports'
    __table_args__ = (
        db.UniqueConstraint('trip_id', 'author_id', name='unique_trip_report_per_author'),
    )
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Report content
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)  # Rich text content
    summary = db.Column(db.String(500))  # Short summary for listings
    
    # Weather and conditions
    weather_conditions = db.Column(db.String(200))
    trail_conditions = db.Column(db.String(200))
    
    # Report metadata
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    featured = db.Column(db.Boolean, default=False, nullable=False)  # Featured on homepage
    
    # Foreign keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='trip_reports', lazy=True)
    photos = db.relationship('Photo', backref='trip_report', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='trip_report', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TripReport {self.title}>'
    
    @property
    def photo_count(self):
        """Get count of photos in this report"""
        return len(self.photos)
    
    @property
    def comment_count(self):
        """Get count of comments on this report"""
        return len([c for c in self.comments if c.is_approved])
    
    @property
    def cover_photo(self):
        """Get the first photo as cover photo"""
        return self.photos[0] if self.photos else None
    
    def can_edit(self, user):
        """Check if user can edit this report"""
        return (user.id == self.author_id or 
                user.is_admin() or 
                (user.is_trip_leader() and user.id == self.trip.leader_id))
    
    def can_delete(self, user):
        """Check if user can delete this report"""
        return user.id == self.author_id or user.is_admin()
    
    @staticmethod
    def get_recent_reports(limit=10):
        """Get recent published trip reports"""
        return TripReport.query.filter_by(is_published=True)\
            .order_by(TripReport.created_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_featured_reports():
        """Get featured trip reports"""
        return TripReport.query.filter_by(is_published=True, featured=True)\
            .order_by(TripReport.created_at.desc()).all()
    
    @staticmethod
    def get_reports_by_author(author_id):
        """Get all reports by specific author"""
        return TripReport.query.filter_by(author_id=author_id)\
            .order_by(TripReport.created_at.desc()).all()
    
    def to_dict(self):
        """Convert report to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'author': self.author.name,
            'trip_title': self.trip.title,
            'photo_count': self.photo_count,
            'comment_count': self.comment_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'cover_photo_url': self.cover_photo.thumbnail_url if self.cover_photo else None
        }


class Photo(db.Model):
    """Photo model for trip report images stored on AWS S3"""
    
    __tablename__ = 'photos'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Photo details
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    caption = db.Column(db.String(500))
    
    # S3 storage details
    s3_key = db.Column(db.String(500), nullable=False)  # Full S3 object key
    s3_bucket = db.Column(db.String(100), nullable=False)
    thumbnail_s3_key = db.Column(db.String(500))  # Thumbnail version
    
    # Photo metadata
    file_size = db.Column(db.Integer)  # Size in bytes
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    content_type = db.Column(db.String(50))  # MIME type
    
    # Photo organization
    display_order = db.Column(db.Integer, default=0)  # Order in gallery
    
    # Foreign keys
    trip_report_id = db.Column(db.Integer, db.ForeignKey('trip_reports.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_photos', lazy=True)
    comments = db.relationship('Comment', backref='photo', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Photo {self.filename}>'
    
    @property
    def url(self):
        """Get full S3 URL for the photo"""
        # This will be implemented with boto3 presigned URLs
        from flask import current_app
        base_url = f"https://{self.s3_bucket}.s3.{current_app.config.get('AWS_REGION', 'us-east-1')}.amazonaws.com"
        return f"{base_url}/{self.s3_key}"
    
    @property
    def thumbnail_url(self):
        """Get S3 URL for thumbnail version"""
        if not self.thumbnail_s3_key:
            return self.url
        from flask import current_app
        base_url = f"https://{self.s3_bucket}.s3.{current_app.config.get('AWS_REGION', 'us-east-1')}.amazonaws.com"
        return f"{base_url}/{self.thumbnail_s3_key}"
    
    @property
    def comment_count(self):
        """Get count of approved comments on this photo"""
        return len([c for c in self.comments if c.is_approved])
    
    def can_edit(self, user):
        """Check if user can edit this photo"""
        return (user.id == self.uploaded_by or 
                user.is_admin() or 
                user.id == self.trip_report.author_id)
    
    def can_delete(self, user):
        """Check if user can delete this photo"""
        return (user.id == self.uploaded_by or 
                user.is_admin() or 
                user.id == self.trip_report.author_id)
    
    def generate_s3_key(self, trip_report_id, filename):
        """Generate S3 key for photo storage"""
        from datetime import datetime
        import uuid
        
        # Create unique filename to avoid conflicts
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Organize by year/month/report
        date_path = datetime.utcnow().strftime('%Y/%m')
        return f"trip-reports/{date_path}/report-{trip_report_id}/{unique_filename}"
    
    def delete_from_s3(self):
        """Delete photo and thumbnail from S3"""
        # This will be implemented with boto3
        # For now, just mark for deletion
        pass
    
    @staticmethod
    def get_recent_photos(limit=20):
        """Get recently uploaded photos"""
        return Photo.query.order_by(Photo.created_at.desc()).limit(limit).all()
    
    def to_dict(self):
        """Convert photo to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'filename': self.filename,
            'caption': self.caption,
            'url': self.url,
            'thumbnail_url': self.thumbnail_url,
            'width': self.width,
            'height': self.height,
            'file_size': self.file_size,
            'comment_count': self.comment_count,
            'uploaded_by': self.uploader.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CommentType(Enum):
    """Comment type enumeration"""
    TRIP = 'trip'            # Trip announcement comments
    TRIP_REPORT = 'trip_report'
    PHOTO = 'photo'


class Comment(db.Model):
    """Comment model for trip announcements, trip reports and photos"""
    
    __tablename__ = 'comments'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Comment content
    content = db.Column(db.Text, nullable=False)
    
    # Comment type and target
    comment_type = db.Column(db.Enum(CommentType), nullable=False)
    
    # Foreign keys (polymorphic - one of these will be set based on comment_type)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=True)
    trip_report_id = db.Column(db.Integer, db.ForeignKey('trip_reports.id'), nullable=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Comment moderation
    is_approved = db.Column(db.Boolean, default=True, nullable=False)  # Auto-approve for now
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='comments', lazy=True)
    
    def __repr__(self):
        if self.trip_id:
            target = 'trip'
        elif self.trip_report_id:
            target = 'report'
        else:
            target = 'photo'
        return f'<Comment by {self.author.name} on {target}>'
    
    def can_edit(self, user):
        """Check if user can edit this comment"""
        return user.id == self.author_id or user.is_admin()
    
    def can_delete(self, user):
        """Check if user can delete this comment"""
        # Import here to avoid circular imports
        from models.trip import Trip
        
        if user.id == self.author_id or user.is_admin():
            return True
        
        # Trip leaders can delete comments on their trip announcements
        if self.trip_id:
            trip = Trip.query.get(self.trip_id)
            return trip and user.id == trip.leader_id
        
        # Trip report authors can delete comments on their reports
        if self.trip_report_id:
            return user.id == self.trip_report.author_id
        
        # Photo owners can delete comments on their photos
        if self.photo_id:
            return user.id == self.photo.trip_report.author_id
        
        return False
    
    @staticmethod
    def get_recent_comments(limit=10):
        """Get recent approved comments"""
        return Comment.query.filter_by(is_approved=True)\
            .order_by(Comment.created_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_comments_for_trip(trip_id):
        """Get all approved comments for a trip announcement"""
        return Comment.query.filter_by(
            trip_id=trip_id,
            is_approved=True
        ).order_by(Comment.created_at).all()
    
    @staticmethod
    def get_comments_for_report(trip_report_id):
        """Get all approved comments for a trip report"""
        return Comment.query.filter_by(
            trip_report_id=trip_report_id,
            is_approved=True
        ).order_by(Comment.created_at).all()
    
    @staticmethod
    def get_comments_for_photo(photo_id):
        """Get all approved comments for a photo"""
        return Comment.query.filter_by(
            photo_id=photo_id,
            is_approved=True
        ).order_by(Comment.created_at).all()
    
    def to_dict(self):
        """Convert comment to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.name,
            'comment_type': self.comment_type.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'can_edit': False,  # Will be set based on current user
            'can_delete': False  # Will be set based on current user
        }


class EventCategory(Enum):
    """Historical event category enumeration"""
    FIRST_ASCENT = 'first_ascent'
    TRAGEDY = 'tragedy'
    DISCOVERY = 'discovery'
    ACHIEVEMENT = 'achievement'
    EXPEDITION = 'expedition'


class HistoricalEvent(db.Model):
    """Historical mountaineering events for 'Na ta dan v zgodovini' feature"""
    
    __tablename__ = 'historical_events'
    __table_args__ = (
        db.UniqueConstraint('date', 'year', name='unique_event_per_date'),
        db.Index('idx_historical_events_date', 'date'),
        db.Index('idx_historical_events_year', 'year'),
        db.Index('idx_historical_events_category', 'category'),
    )
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Event timing
    date = db.Column(db.String(10), nullable=False)  # Format: "July 26" 
    year = db.Column(db.Integer, nullable=False)
    
    # Event content
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200))
    
    # People involved (stored as JSON array)
    people = db.Column(db.JSON, default=list)  # ["name1", "name2"]
    
    # Source and categorization
    url = db.Column(db.String(500))  # Primary source URL (backward compatibility)
    url_secondary = db.Column(db.String(500))  # Secondary source URL
    category = db.Column(db.Enum(EventCategory), nullable=False)
    
    # Research methodology tracking
    methodology = db.Column(db.Text)  # Research methodology used
    url_methodology = db.Column(db.Text)  # Source credibility reasoning
    
    # Content management
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_generated = db.Column(db.Boolean, default=True, nullable=False)  # True if AI-generated
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<HistoricalEvent {self.date} {self.year}: {self.title}>'
    
    @property
    def full_date_string(self):
        """Get formatted date string"""
        return f"{self.date}, {self.year}"
    
    @property
    def people_list(self):
        """Get people as list (handle None case)"""
        return self.people if self.people else []
    
    @property
    def people_names(self):
        """Get people names as comma-separated string"""
        if not self.people:
            return ""
        return ", ".join(self.people)
    
    @staticmethod
    def get_event_for_date(date_string):
        """Get historical event for specific date (e.g., 'July 26')"""
        return HistoricalEvent.query.filter_by(date=date_string).first()
    
    @staticmethod
    def get_todays_event():
        """Get historical event for today's date"""
        from datetime import datetime
        from utils.llm_service import format_date_standard
        today = format_date_standard(datetime.now())
        return HistoricalEvent.get_event_for_date(today)
    
    @staticmethod
    def get_featured_events(limit=5):
        """Get featured historical events"""
        return HistoricalEvent.query.filter_by(is_featured=True)\
            .order_by(HistoricalEvent.year.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_events_by_category(category, limit=10):
        """Get events by category"""
        return HistoricalEvent.query.filter_by(category=category)\
            .order_by(HistoricalEvent.year.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_recent_events(limit=30):
        """Get recently added events"""
        return HistoricalEvent.query.order_by(HistoricalEvent.created_at.desc())\
            .limit(limit).all()
    
    def can_edit(self, user):
        """Check if user can edit this event"""
        return user.is_admin()
    
    def can_delete(self, user):
        """Check if user can delete this event"""
        return user.is_admin()
    
    def to_dict(self):
        """Convert event to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'date': self.date,
            'year': self.year,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'people': self.people_list,
            'url': self.url,
            'category': self.category.value,
            'is_featured': self.is_featured,
            'full_date': self.full_date_string,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class NewsCategory(Enum):
    """News item category enumeration"""
    SAFETY = 'safety'
    CONDITIONS = 'conditions'
    ACHIEVEMENTS = 'achievements'
    GEAR = 'gear'
    EVENTS = 'events'


class NewsItem(db.Model):
    """News items for daily mountaineering news curation (Future Phase 3B)"""
    
    __tablename__ = 'news_items'
    __table_args__ = (
        db.Index('idx_news_items_date', 'news_date'),
        db.Index('idx_news_items_category', 'category'),
        db.Index('idx_news_items_relevance', 'relevance_score'),
    )
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # News content
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(NewsCategory), nullable=False)
    
    # Source information
    url = db.Column(db.String(500))  # Source article URL
    source_name = db.Column(db.String(100))  # E.g., "Climbing.com", "Outside Magazine"
    
    # Relevance and dating
    relevance_score = db.Column(db.Float, default=0.0)  # AI-determined relevance 0-1
    news_date = db.Column(db.Date, nullable=False)  # When the news happened
    
    # Content lifecycle
    expires_at = db.Column(db.DateTime)  # When this news becomes stale
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_generated = db.Column(db.Boolean, default=True, nullable=False)  # True if AI-curated
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NewsItem {self.news_date}: {self.title}>'
    
    @property
    def is_expired(self):
        """Check if this news item has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def age_days(self):
        """Get age of news in days"""
        from datetime import date
        return (date.today() - self.news_date).days
    
    @staticmethod
    def get_current_news(limit=5):
        """Get current (non-expired) news items"""
        from datetime import datetime
        return NewsItem.query.filter(
            db.or_(
                NewsItem.expires_at.is_(None),
                NewsItem.expires_at > datetime.utcnow()
            )
        ).order_by(
            NewsItem.relevance_score.desc(),
            NewsItem.news_date.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_todays_news():
        """Get today's generated news items"""
        from datetime import date
        return NewsItem.query.filter_by(news_date=date.today())\
            .order_by(NewsItem.relevance_score.desc()).all()
    
    @staticmethod
    def get_news_by_category(category, limit=10):
        """Get news by category"""
        return NewsItem.query.filter_by(category=category)\
            .filter(
                db.or_(
                    NewsItem.expires_at.is_(None),
                    NewsItem.expires_at > datetime.utcnow()
                )
            ).order_by(NewsItem.relevance_score.desc())\
            .limit(limit).all()
    
    @staticmethod
    def cleanup_expired_news():
        """Remove expired news items (for maintenance)"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)  # Keep for 30 days after expiry
        expired_items = NewsItem.query.filter(
            NewsItem.expires_at < cutoff_date
        ).all()
        
        for item in expired_items:
            db.session.delete(item)
        
        return len(expired_items)
    
    def can_edit(self, user):
        """Check if user can edit this news item"""
        return user.is_admin()
    
    def can_delete(self, user):
        """Check if user can delete this news item"""
        return user.is_admin()
    
    def to_dict(self):
        """Convert news item to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'category': self.category.value,
            'url': self.url,
            'source_name': self.source_name,
            'relevance_score': self.relevance_score,
            'news_date': self.news_date.isoformat() if self.news_date else None,
            'age_days': self.age_days,
            'is_featured': self.is_featured,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }