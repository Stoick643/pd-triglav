import os
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    """Base configuration class"""

    # Flask core settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Database configuration
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        # Handle PostgreSQL URL format for SQLAlchemy
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Development fallback to SQLite in databases directory
        db_dir = os.path.join(basedir, "databases")
        os.makedirs(db_dir, exist_ok=True)  # Ensure databases directory exists
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(db_dir, "development.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # AWS S3 configuration
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.environ.get("AWS_REGION", "eu-north-1")
    AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET")
    AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL")

    # Email configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() in ["true", "1", "yes"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # LLM API configuration
    LLM_API_KEY = os.environ.get("LLM_API_KEY")
    LLM_API_URL = os.environ.get("LLM_API_URL")
    MOONSHOT_API_KEY = os.environ.get("MOONSHOT_API_KEY")
    MOONSHOT_API_URL = os.environ.get("MOONSHOT_API_URL")
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

    # News API configuration
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

    # Application settings
    POSTS_PER_PAGE = 10
    PHOTOS_PER_PAGE = 20
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB total upload limit for multiple photos

    # Photo upload settings
    MAX_PHOTOS_PER_REPORT = 10
    MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB per individual photo
    ALLOWED_PHOTO_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory database for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    SERVER_NAME = "localhost.localdomain"


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    SQLALCHEMY_ECHO = False

    # Additional production settings
    PREFERRED_URL_SCHEME = "https"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


# Configuration dictionary for easy access
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
