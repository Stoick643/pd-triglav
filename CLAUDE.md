# CLAUDE.md - Development Context & Commands

## Project Context

**PD Triglav Mountaineering Club Web Application**
- Python Flask web app for Slovenian mountaineering club (~200 members)
- Features: Member management, trip announcements, trip reports, photo galleries
- AI-powered historical content and mountaineering news
- Deployment: Render platform with GitHub integration
- Database: PostgreSQL (production), SQLite (development)
- File Storage: AWS S3 for photos

## Key Decisions Made

### Technology Stack
- **Backend**: Flask + SQLAlchemy + PostgreSQL
- **Frontend**: Jinja2 + Bootstrap 5 + HTMX + TinyMCE
- **Auth**: Flask-Login + Authlib (Google OAuth)
- **File Storage**: AWS S3 + Boto3 + Pillow
- **Email**: Flask-Mail with threading
- **Testing**: pytest + coverage

### User Roles & Permissions
1. **Pending Member**: Limited access until admin approval
2. **Member**: Full access to trips, reports, comments
3. **Trip Leader**: Can create/manage trips + member permissions
4. **Admin**: Full system access + user management

### Development Approach
- **Phases**: 4 MVP phases (Auth → Trips → Reports → AI features)
- **Testing**: Unit + integration tests, ~70% coverage target
- **Language**: Slovenian throughout the application
- **Design**: Web-first with mobile support

## Essential Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install pip-tools and sync dependencies
pip install pip-tools
pip-sync requirements.txt

# Environment variables
cp .env.example .env
# Edit .env with actual values
```

### Dependency Management (pip-tools)
```bash
# Add new dependency
echo "new-package" >> requirements.in
pip-compile requirements.in
pip-sync requirements.txt

# Update all dependencies to latest versions
pip-compile --upgrade requirements.in
pip-sync requirements.txt

# Generate requirements.txt from requirements.in
pip-compile requirements.in

# Sync environment to match requirements.txt exactly
pip-sync requirements.txt
```

**Important**: Always edit `requirements.in`, never `requirements.txt` directly.

### Database Operations
```bash
# Initialize database
flask db init

# Create migration
flask db migrate -m "Description"

# Apply migrations  
flask db upgrade

# Seed test data
python3 scripts/seed_db.py
```

### Development Server
```bash
# Run Flask development server
python3 app.py

# Alternative using flask command
export FLASK_ENV=development
flask run --debug

# Or using flask run
flask run
```

### Testing

**Fast Development Testing (~1-2 minutes):**
```bash
# Method 1: Using make (recommended)
make test-fast

# Method 2: Using script
./scripts/test-runner.sh fast

# Method 3: Direct pytest
pytest -m "fast" -v
```

**Specific Test Categories:**
```bash
# Security tests only
make test-security

# API endpoint tests
make test-api

# Database model tests
make test-models

# Authentication tests
make test-auth
```

**Full Test Suite (~8+ minutes):**
```bash
# All tests (use before commits)
make test-all

# With coverage report
make test-coverage
```

**Test Organization:**
- **Fast tests** (`pytest -m "fast"`): Models, forms, basic routes - for daily development
- **Slow tests** (`pytest -m "slow"`): External services (LLM, S3, OAuth) - for CI/pre-commit
- **Integration tests** (`pytest -m "integration"`): Real API calls - for comprehensive testing
- **Security tests** (`pytest -m "security"`): CSRF, XSS, authentication bypasses

**Legacy Commands:**
```bash
# Run all tests (old way - slow)
pytest

# Run specific test file
pytest tests/test_auth.py
```

### Code Quality
```bash
# Linting (if configured)
flake8 .

# Code formatting (if configured)  
black .

# Type checking (if configured)
mypy .
```

### Git Workflow
```bash
# Standard workflow
git add .
git commit -m "Description"
git push origin main

# Feature branch workflow
git checkout -b feature/new-feature
# ... make changes ...
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
# Create PR on GitHub
```

## Test Users (Development)

When `scripts/seed_db.py` is run, these test users are created:

- **admin@pd-triglav.si** / password123 (Admin role)
- **clan@pd-triglav.si** / password123 (Member role)
- **vodnik@pd-triglav.si** / password123 (Trip Leader role)  
- **pending@pd-triglav.si** / password123 (Pending approval)

## Database Organization

All database files are organized in the `databases/` directory:

```
databases/
├── development.db       # Main development database
├── test_main_abc123.db  # Test databases (auto-generated)
├── test_worker1_def.db  # Parallel test worker databases
├── .gitkeep            # Ensures directory is tracked
└── README.md           # Database documentation
```

### Database Isolation
- **Development**: `databases/development.db` (persistent, contains seeded data)
- **Testing**: `databases/test_*.db` (temporary, created/destroyed per test)
- **Production**: PostgreSQL (managed by Render)

### Key Benefits
- All project databases in one location
- Complete test isolation from development
- Easy cleanup and management
- Git-controlled structure (but database files ignored)

## Environment Variables Reference

Required in `.env` file:

```bash
# Flask Core
SECRET_KEY=your-long-random-secret-key
FLASK_ENV=development
DATABASE_URL=postgresql://user:pass@localhost/pd_triglav

# Google OAuth
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# AWS S3 Configuration  
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=eu-north-1
AWS_S3_BUCKET=your-s3-bucket-name
AWS_S3_ENDPOINT_URL=https://s3.eu-north-1.amazonaws.com

# Email (Render SMTP)
MAIL_SERVER=smtp.render.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@domain.com

# LLM Integration (for historical content)
LLM_API_KEY=your-llm-api-key
LLM_API_URL=your-llm-api-endpoint
```

## Project Structure

```
pd-triglav/
├── app.py                 # Flask application factory
├── config.py             # Configuration classes
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in git)
├── models/
│   ├── __init__.py
│   ├── user.py          # User model and auth
│   ├── trip.py          # Trip and participant models  
│   └── content.py       # Reports, photos, comments
├── routes/
│   ├── __init__.py
│   ├── auth.py          # Authentication routes
│   ├── trips.py         # Trip management routes
│   ├── reports.py       # Trip reports and photos
│   └── admin.py         # Admin dashboard
├── templates/
│   ├── base.html        # Base template
│   ├── auth/            # Authentication templates
│   ├── trips/           # Trip-related templates
│   └── reports/         # Report templates
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── migrations/           # Database migrations
├── tests/               # Test files
├── scripts/
│   └── seed_db.py      # Development data seeding
└── docs/               # Documentation
```

## Development Workflow

### Phase 1: Authentication & User Management (Current)
- [x] Basic Flask app structure
- [x] User model with roles
- [x] Classical + Google OAuth registration
- [x] Admin approval workflow
- [x] Role-based access control

### Phase 2: Trip Management (Next)
- [ ] Trip announcements and CRUD
- [ ] Calendar view implementation
- [ ] Trip signup system with waitlists
- [ ] Email notifications

### Phase 3: Content & Photos
- [ ] Trip reports with rich text
- [ ] AWS S3 photo upload
- [ ] Comments system
- [ ] Photo galleries

### Phase 4: AI Features
- [ ] Historical events integration
- [ ] Mountaineering news summary
- [ ] Search functionality

## Common Issues & Solutions

### Database Issues
```bash
# Reset database (development only)
rm databases/development.db  # Remove development database
flask db upgrade

# Reset all test databases
rm databases/test_*.db

# Fix migration conflicts
flask db stamp head
flask db migrate -m "Fix migration"
```

### AWS S3 Issues
- Check bucket permissions and CORS configuration
- Verify AWS credentials in .env file
- Test with boto3 client directly

### OAuth Issues  
- Verify Google OAuth credentials
- Check redirect URIs in Google Console
- Ensure HTTPS in production

## Deployment Notes

### Render Configuration
- Uses `render.yaml` for deployment configuration
- Environment variables set in Render dashboard
- Automatic deployments on git push to main
- PostgreSQL database managed by Render

### Production Considerations
- Set `FLASK_ENV=production` in production
- Use strong `SECRET_KEY` value
- Configure proper error logging
- Set up database backups
- Monitor AWS S3 usage and costs

## Testing Strategy

- **Unit Tests**: Models, utility functions
- **Integration Tests**: Authentication flows, database operations
- **Functional Tests**: End-to-end user workflows
- **API Tests**: AJAX endpoints and external integrations

Target: ~70% test coverage on core functionality.

## Security Checklist

- [x] Environment variables for secrets
- [x] CSRF protection with Flask-WTF
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] Secure password hashing
- [x] File upload validation
- [x] Session security configuration

## Performance Considerations

- Database indexing on frequently queried fields
- Image compression and thumbnail generation  
- Pagination for large result sets
- Caching for static content and repeated queries
- Background tasks for email sending (threading initially)

---

*This file serves as a quick reference for development context and common operations. Update as the project evolves.*