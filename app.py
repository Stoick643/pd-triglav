from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

# Initialize Flask extensions
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Trust proxy headers (Fly.io / reverse proxy) so url_for generates https:// URLs
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Import db after app creation to avoid circular imports
    from models.user import db

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Prosim prijavite se za dostop do te strani."
    login_manager.login_message_category = "info"

    # Import models (needed for database creation)
    from models.user import User

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.main import bp as main_bp

    app.register_blueprint(main_bp)

    from routes.auth import bp as auth_bp, init_oauth

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from routes.trips import bp as trips_bp

    app.register_blueprint(trips_bp, url_prefix="/trips")

    from routes.reports import bp as reports_bp

    app.register_blueprint(reports_bp, url_prefix="/reports")

    # Initialize OAuth
    init_oauth(app)

    # Add custom Jinja2 filters
    @app.template_filter("markdown")
    def markdown_filter(text):
        """Simple Markdown filter for basic formatting"""
        if not text:
            return ""

        import re

        # Convert **bold** to <strong>bold</strong>
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

        # Convert *italic* to <em>italic</em>
        text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)

        # Convert line breaks to <br> tags
        text = text.replace("\n", "<br>")

        return text

    # Initialize background scheduler for daily tasks
    try:
        from utils.scheduler import init_scheduler

        with app.app_context():
            scheduler = init_scheduler(app)
            if scheduler:
                app.scheduler = scheduler
    except Exception as e:
        app.logger.error(f"Failed to initialize scheduler: {e}")

    # Initialize database on startup (for Fly.io deployment)
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created/verified")
            
            # Seed admin user if not exists
            from models.user import UserRole
            admin_email = "admin@pd-triglav.si"
            if not User.query.filter_by(email=admin_email).first():
                admin = User.create_user(
                    email=admin_email,
                    name="Administrator PD Triglav",
                    password="password123",
                    role=UserRole.ADMIN,
                )
                if admin:
                    admin.approve(UserRole.ADMIN)
                    db.session.commit()
                    app.logger.info(f"Admin user created: {admin_email}")
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")

    return app


# For development server
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
