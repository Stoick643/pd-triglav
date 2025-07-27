from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

# Initialize Flask extensions
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Import db after app creation to avoid circular imports
    from models.user import db
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Prosim prijavite se za dostop do te strani.'
    login_manager.login_message_category = 'info'
    
    # Import models (needed for database creation)
    from models.user import User
    from models.trip import Trip, TripParticipant
    from models.content import TripReport, Photo, Comment, HistoricalEvent, NewsItem
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from routes.auth import bp as auth_bp, init_oauth
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from routes.trips import bp as trips_bp
    app.register_blueprint(trips_bp, url_prefix='/trips')
    
    from routes.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Initialize OAuth
    init_oauth(app)
    
    # Exempt auth routes from CSRF protection (they use raw forms)
    csrf.exempt(auth_bp)
    
    # Add custom Jinja2 filters
    @app.template_filter('markdown')
    def markdown_filter(text):
        """Simple Markdown filter for basic formatting"""
        if not text:
            return ''
        
        import re
        
        # Convert **bold** to <strong>bold</strong>
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        
        # Convert *italic* to <em>italic</em>
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        
        # Convert line breaks to <br> tags
        text = text.replace('\n', '<br>')
        
        return text
    
    # Database tables are now managed by Flask-Migrate
    # Use 'flask db upgrade' to create/update tables
    
    return app


# For development server
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)