from flask import Flask, render_template
from flask_login import LoginManager
from config import Config

# Initialize Flask extensions
login_manager = LoginManager()


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Import db after app creation to avoid circular imports
    from models.user import db
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Prosim prijavite se za dostop do te strani.'
    login_manager.login_message_category = 'info'
    
    # Import models (needed for migrations)
    from models.user import User
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


# For development server
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)