# PD Triglav - Mountaineering Club Web Application

Web application for PD Triglav mountaineering club built with Python Flask. Features member management, trip announcements, trip reports with photo galleries, and AI-powered historical content.

## Features

- **Multi-role Authentication**: Classical registration + Google OAuth with admin approval
- **Trip Management**: Announcements, signup system, calendar view
- **Rich Content**: Trip reports with photo galleries and comments
- **AI-Powered Content**: Daily historical events and mountaineering news
- **Responsive Design**: Mobile-friendly web interface
- **Slovenian Language**: Built for Slovenian mountaineering community

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (or SQLite for development)
- AWS S3 account (for photo storage)
- Google OAuth credentials

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Stoick643/pd-triglav.git
cd pd-triglav
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment setup**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database setup**
```bash
flask db upgrade
python3 scripts/seed_db.py  # Creates test users
```

6. **Run the application**
```bash
python3 app.py
# Or alternatively: flask run
```

Visit `http://localhost:5000` to access the application.

### Test Users (Development)
- **Admin**: admin@pd-triglav.si / password123
- **Member**: clan@pd-triglav.si / password123  
- **Trip Leader**: vodnik@pd-triglav.si / password123
- **Pending**: pending@pd-triglav.si / password123

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
DATABASE_URL=postgresql://user:pass@localhost/pd_triglav

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=eu-north-1
AWS_S3_BUCKET=pd-triglav-photos

# Email Configuration
MAIL_SERVER=smtp.render.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password

# LLM API (for historical content)
LLM_API_KEY=your-llm-api-key
LLM_API_URL=your-llm-endpoint
```

## Project Structure

```
pd-triglav/
├── app.py                 # Flask application factory
├── config.py             # Configuration classes
├── requirements.txt      # Python dependencies
├── models/               # Database models
├── routes/               # Application routes
├── templates/            # Jinja2 templates
├── static/               # CSS, JavaScript, images
├── migrations/           # Database migrations
├── tests/                # Test files
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

### Code Quality
```bash
# Run linting
flake8 .

# Format code
black .
```

## Deployment

### Render Deployment
1. Connect your GitHub repository to Render
2. Configure environment variables in Render dashboard
3. Deploy using the provided `render.yaml` configuration

### Manual Deployment
See `docs/deployment.md` for detailed deployment instructions.

## Documentation

- **[Project Specification](docs/specification.md)** - Complete feature requirements
- **[Development Plan](docs/development-plan.md)** - Implementation phases and guidelines
- **[API Documentation](docs/api.md)** - API endpoints and usage
- **[User Guide](docs/user-guide.md)** - How to use the application

## Technology Stack

- **Backend**: Python Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Jinja2, Bootstrap 5, HTMX
- **Authentication**: Flask-Login, Authlib (Google OAuth)
- **File Storage**: AWS S3
- **Deployment**: Render
- **Testing**: pytest, coverage

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions or issues, please:
1. Check the [documentation](docs/)
2. Search existing [GitHub issues](https://github.com/Stoick643/pd-triglav/issues)
3. Create a new issue if needed

## Acknowledgments

- PD Triglav mountaineering club for project requirements
- Flask community for excellent documentation
- Contributors and testers