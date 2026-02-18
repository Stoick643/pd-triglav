# CLAUDE.md - Development Context & Commands

## Project Context

**PD Triglav Mountaineering Club Web Application**
- Python Flask web app for Slovenian mountaineering club (~200 members)
- Features: Member management, trip announcements, trip reports, photo galleries
- AI-powered historical content and mountaineering news
- Deployment: Fly.io with buildpacks (auto-detect Python)
- Database: SQLite (production on persistent volume at /data/, development local)
- File Storage: AWS S3 for photos

## Key Decisions Made

### Technology Stack
- **Backend**: Flask + SQLAlchemy + SQLite
- **Frontend**: Jinja2 + Bootstrap 5 + vanilla JS + TinyMCE
- **Auth**: Flask-Login + Authlib (Google OAuth)
- **File Storage**: AWS S3 + Boto3 + Pillow
- **Email**: Flask-Mail with Amazon SES
- **AI/LLM**: Anthropic Claude + Moonshot Kimi K2.5 + DeepSeek (multi-provider with fallback)
- **News**: RSS feeds (PZS, Gore & Ljudje, PlanetMountain, etc.) + NewsAPI fallback
- **Testing**: pytest + coverage
- **Deployment**: Fly.io with buildpacks (no Docker)

### User Roles & Permissions
1. **Pending Member**: Limited access until admin approval
2. **Member**: Full access to trips, reports, comments
3. **Trip Leader**: Can create/manage trips + member permissions
4. **Admin**: Full system access + user management

### LLM Provider Priority (use-case dependent)

| Priority | Historical events | Everything else |
|----------|-------------------|-----------------|
| 1st | Claude Sonnet 4.6 | Kimi K2.5 |
| 2nd | Kimi K2.5 | DeepSeek |
| 3rd | DeepSeek | Claude Sonnet 4.6 |

### Development Approach
- **Testing**: Unit + integration tests, ~70% coverage target
- **Language**: Slovenian throughout the application (including AI-generated content)
- **Design**: Web-first with mobile support, corporate design identity

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
# Add new dependency: edit requirements.in, then:
pip-compile requirements.in
pip-sync requirements.txt

# Update all dependencies
pip-compile --upgrade requirements.in
pip-sync requirements.txt
```

**Important**: Always edit `requirements.in`, never `requirements.txt` directly.

### Database Operations

**Development (Local):**
```bash
python scripts/init_db.py        # Initialize database (create tables)
python scripts/seed_db.py        # Seed dev data (4 test users + sample trips)
python scripts/import_historical_events.py  # Import 52 curated events
```

**Production (Fly.io):**
```bash
fly ssh console
python scripts/init_db.py                    # Re-init (idempotent)
python scripts/import_historical_events.py   # Import curated events
python /data/q.py "SELECT * FROM users"      # Query DB (helper script on volume)
```

### Development Server
```bash
python app.py
# or
flask run --debug
```

### Testing

**Fast Development Testing:**
```bash
make test-fast
# or
pytest -m "fast" -v
```

**Specific Test Categories:**
```bash
make test-security    # Security tests
make test-api         # API endpoint tests
make test-models      # Database model tests
make test-auth        # Authentication tests
```

**Full Test Suite:**
```bash
make test-all
make test-coverage    # With coverage report
```

**Historical Events Tests (60 tests):**
```bash
pytest tests/test_historical_events_model.py tests/test_content_generation.py tests/test_historical_events_routes.py -v
```

### Git Workflow
```bash
git add .
git commit -m "Description"
git push origin master    # Auto-deploys to Fly.io via GitHub
```

## Test Users (Development)

When `scripts/seed_db.py` is run:
- **admin@pd-triglav.si** / password123 (Admin role)
- **clan@pd-triglav.si** / password123 (Member role)
- **vodnik@pd-triglav.si** / password123 (Trip Leader role)
- **pending@pd-triglav.si** / password123 (Pending approval)

## Database Organization

```
databases/
├── pd_triglav.db    # Main development database
├── test.db          # Test database
└── .gitkeep
```

- **Development**: `databases/pd_triglav.db` (persistent, seeded data)
- **Testing**: `databases/test.db` (single mode) or `databases/test_gw*.db` (parallel)
- **Production**: SQLite at `/data/pd_triglav.db` on Fly.io persistent volume

## Environment Variables Reference

Required in `.env` file:

```bash
# Flask Core
SECRET_KEY=your-long-random-secret-key
FLASK_ENV=development

# Google OAuth
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=eu-north-1
AWS_S3_BUCKET=your-s3-bucket-name
AWS_S3_ENDPOINT_URL=https://s3.eu-north-1.amazonaws.com

# Email (Amazon SES)
MAIL_SERVER=email-smtp.eu-north-1.amazonaws.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-ses-smtp-username
MAIL_PASSWORD=your-ses-smtp-password
MAIL_DEFAULT_SENDER=your-email@domain.com

# LLM Providers (for AI content generation)
ANTHROPIC_API_KEY=sk-ant-...          # Claude Sonnet 4.6 (primary for historical)
MOONSHOT_API_KEY=sk-...               # Kimi K2.5 (primary for news/general)
DEEPSEEK_API_KEY=sk-...               # DeepSeek (fallback)

# News
NEWS_API_KEY=your-newsapi-key         # NewsAPI fallback
```

## Project Structure

```
pd-triglav/
├── app.py                 # Flask application factory + scheduler init
├── config.py              # Configuration classes
├── fly.toml               # Fly.io deployment config
├── requirements.in        # Dependency source (edit this)
├── requirements.txt       # Compiled dependencies (auto-generated)
├── models/
│   ├── user.py            # User model, roles, auth
│   ├── trip.py            # Trip and participant models
│   └── content.py         # HistoricalEvent, DailyNews, EventCategory
├── routes/
│   ├── main.py            # Homepage, history, news, admin actions, API endpoints
│   ├── auth.py            # Authentication routes
│   └── trips.py           # Trip management routes
├── utils/
│   ├── llm_providers.py   # AnthropicProvider, MoonshotProvider, DeepSeekProvider, ProviderManager
│   ├── llm_service.py     # LLMService (prompt loading, event generation, news)
│   ├── content_generation.py  # HistoricalEventService, ContentManager
│   ├── daily_news.py      # RSS aggregation, web scraping, NewsAPI fallback
│   ├── history_prompt.md  # LLM prompt template for historical events (Slovenian)
│   ├── hero_utils.py      # Hero image selection (seasonal/time-based)
│   └── scheduler.py       # APScheduler daily tasks (6 AM)
├── templates/
│   ├── base.html          # Base template with sidebar navigation
│   ├── index.html         # Hero landing page + events + news (with JS polling)
│   ├── history/           # Historical event detail
│   ├── auth/              # Login, register, pending
│   └── trips/             # Trip templates
├── static/
│   ├── css/               # design-system, app, components, sidebar, lightbox, modals
│   ├── js/                # app, hero, lightbox, confirm-modal, trip-modal
│   └── images/hero/       # Seasonal hero images
├── scripts/
│   ├── init_db.py         # Production DB init (db.create_all + admin)
│   ├── seed_db.py         # Development data seeding
│   ├── seed_db_prod.py    # Production seeding (admin only)
│   ├── import_historical_events.py  # Import 52 curated events from JSON
│   └── migrate_dates_to_structured.py  # One-time migration (string->int dates)
├── tests/                 # pytest test files
├── databases/             # Local SQLite databases
└── docs/                  # Documentation
```

## Development Status

### Completed ✅
- **Authentication & User Management**: Login, register, Google OAuth, admin approval, roles
- **Professional Design**: Corporate identity, sidebar navigation, responsive layout
- **Trip Management**: CRUD, calendar, signup/waitlist, email notifications
- **Hero Landing Page**: Seasonal images, parallax, user-state messaging, CTAs
- **Modal System**: Confirmation modals, trip modals, lightbox
- **Historical Events (Phase 3A)**: 52 curated events, LLM generation, homepage widget, archive
- **Historical Events Data Quality (Phase 3A.1)**: Structured dates, curated priority, confidence filtering, multi-provider LLM, Slovenian output
- **Daily News**: RSS aggregation (PZS, Gore & Ljudje + international), homepage widget
- **Lazy Background Generation**: Both sections generate on first visit, JS polling

### In Progress / Next
- **Content polish**: Verify Slovenian RSS sources work reliably
- **Production monitoring**: Check LLM costs, error rates

### Future Roadmap
- **Trip Reports & Photos**: Rich text editing, S3 photo upload, galleries, comments
- **Advanced AI**: Intelligent search, content recommendations
- **Performance**: Caching, CDN, image optimization
- **Accessibility**: Screen readers, keyboard navigation improvements

## Fly.io Deployment

**App Configuration:**
- **App Name**: pd-triglav
- **Region**: ams (Amsterdam)
- **Domain**: pd-triglav.fly.dev
- **Database**: SQLite at /data/pd_triglav.db (persistent volume)
- **Free tier**: Machine auto-stops when idle, auto-starts on request

**Deploy**: Automatic via GitHub push to master

**Manual deploy**: `flyctl deploy`

**SSH & DB queries:**
```bash
fly machine start              # Wake machine if stopped
fly ssh console                # SSH in
python /data/q.py "SQL HERE"   # Query SQLite (helper on persistent volume)
```

**Secrets:**
```bash
flyctl secrets set SECRET_KEY="..."
flyctl secrets set GOOGLE_CLIENT_ID="..."
flyctl secrets set GOOGLE_CLIENT_SECRET="..."
flyctl secrets set AWS_ACCESS_KEY_ID="..."
flyctl secrets set AWS_SECRET_ACCESS_KEY="..."
flyctl secrets set AWS_REGION="eu-north-1"
flyctl secrets set AWS_S3_BUCKET="..."
flyctl secrets set AWS_S3_ENDPOINT_URL="https://s3.eu-north-1.amazonaws.com"
flyctl secrets set MAIL_SERVER="email-smtp.eu-north-1.amazonaws.com"
flyctl secrets set MAIL_USERNAME="..."
flyctl secrets set MAIL_PASSWORD="..."
flyctl secrets set MAIL_DEFAULT_SENDER="..."
flyctl secrets set ANTHROPIC_API_KEY="..."
flyctl secrets set MOONSHOT_API_KEY="..."
flyctl secrets set DEEPSEEK_API_KEY="..."
flyctl secrets set NEWS_API_KEY="..."
```

**Key behaviors:**
- `db.create_all()` runs on app startup (creates missing tables, doesn't alter existing)
- Scheduler fires at 6 AM (news + historical event) but machine may be sleeping
- Lazy generation: first visitor triggers background generation if content missing
- JS polling refreshes both sections without page reload

## Common Issues & Solutions

### Free Tier Machine Sleeping
Machine auto-stops when idle. Content generation via scheduler may not fire.
**Solution**: Lazy background generation on first visit + JS polling.

### Database Schema Changes
`db.create_all()` won't alter existing tables. For schema changes:
```bash
fly ssh console
python -c "import sqlite3; conn = sqlite3.connect('/data/pd_triglav.db'); conn.execute('DROP TABLE table_name'); conn.commit(); print('Done'); conn.close()"
# Then restart app — db.create_all() recreates with new schema
```

### LLM Low Confidence
If all providers return low-confidence events, a fallback event is created.
Curated events (52 from zsa.si) always take priority over AI-generated ones.

### Moonshot Kimi K2.5
Only allows `temperature=1`. Hardcoded in provider.

## Security Checklist

- [x] Environment variables for secrets
- [x] CSRF protection with Flask-WTF
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] Secure password hashing (scrypt)
- [x] File upload validation
- [x] Session security configuration

---

*Last updated: February 2026. See `docs/development-plan.md` for detailed phase specifications.*
