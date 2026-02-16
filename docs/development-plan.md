# PD Triglav - Development Implementation Plan

## Development Philosophy

This plan serves as a **flexible guideline** rather than rigid requirements. Phases can be adjusted based on user feedback, technical discoveries, and changing priorities. The focus is on delivering working features incrementally while maintaining code quality and documentation.

## MVP Development Phases

### Phase 1: Core Authentication & User Management
**Goal**: Establish secure user authentication and role-based access foundation

#### Features to Implement
- [x] Flask application structure with blueprints
- [x] PostgreSQL database setup with SQLAlchemy
- [x] User model with roles (pending, member, trip_leader, admin)
- [x] Classical registration (email/password)
- [x] Google OAuth integration
- [x] Admin approval workflow
- [x] Session management with Flask-Login
- [x] Role-based access control
- [x] Basic responsive layout with Bootstrap 5

#### Database Models
```python
# User model
class User(db.Model):
    id, email, password_hash, name
    role (enum: pending, member, trip_leader, admin)
    is_approved (boolean)
    google_id (optional)
    created_at, last_login
```

#### Key Routes
- `/` - Home page (role-based content)
- `/auth/register` - Classical registration
- `/auth/login` - Login form
- `/auth/google` - Google OAuth
- `/admin/users` - User management (admin only)

#### Testing Requirements
- User registration flow
- OAuth authentication
- Admin approval process
- Role-based access restrictions

#### Phase 1 Definition of Done
- New users can register via email or Google
- Admin can approve/reject pending members
- Different content shown based on user role
- All authentication flows working securely

---

### Phase 2: Trip Management & Calendar
**Goal**: Core trip functionality with announcements and signup system

#### Features to Implement
- [x] Trip model and CRUD operations
- [x] Trip announcements (create, edit, view)
- [x] Trip signup system with waitlists
- [x] Calendar view (upcoming and past trips)
- [x] Email notifications for new trips
- [x] Trip leader permissions and management
- [x] Basic trip details (difficulty, equipment, etc.)

#### Database Models
```python
# Trip model
class Trip(db.Model):
    id, title, description, date, difficulty_level
    meeting_point, equipment_needed, cost_info
    created_by (trip_leader_id)
    status (announced, completed, cancelled)
    created_at, updated_at

# TripParticipant model (many-to-many)
class TripParticipant(db.Model):
    trip_id, user_id, signup_date
    status (confirmed, waitlist)
```

#### Key Routes
- `/trips` - Trip listings
- `/trips/create` - New trip (trip leaders only)
- `/trips/<id>` - Trip details and signup
- `/calendar` - Calendar view
- `/api/trips/signup` - AJAX signup endpoint

#### Email Integration
- Flask-Mail setup with threading
- Trip announcement notifications
- Signup confirmation emails
- Waitlist notifications

#### Phase 2 Definition of Done
- Trip leaders can create and manage trips
- Members can sign up for trips instantly
- Calendar displays upcoming and past events
- Email notifications working reliably

---

### Phase 3: Trip Reports & Photo System
**Goal**: Content creation with rich trip reports and photo management

#### Features to Implement
- [x] Trip reports with rich text editor
- [x] AWS S3 integration for photo uploads
- [x] Image processing (thumbnails, compression)
- [x] Photo galleries and display
- [x] Comments system on reports and photos
- [x] Photo tagging functionality
- [x] Content moderation capabilities

#### Database Models
```python
# TripReport model
class TripReport(db.Model):
    id, trip_id, author_id, title, content
    created_at, updated_at, is_published

# Photo model  
class Photo(db.Model):
    id, trip_report_id, filename, s3_key
    caption, uploaded_by, created_at
    thumbnail_s3_key

# Comment model
class Comment(db.Model):
    id, content_type (trip_report, photo)
    content_id, author_id, content
    created_at, is_approved
```

#### AWS S3 Integration
- Boto3 setup and configuration
- Image upload with progress indication
- Thumbnail generation with Pillow
- Secure file access with presigned URLs

#### Rich Text Editor
- TinyMCE integration
- Image embedding in reports
- Content sanitization
- Mobile-friendly editing

#### Phase 3 Definition of Done
- Members can create detailed trip reports
- Photos upload to S3 and display in galleries
- Comments work like social media
- Content moderation tools available

---

### Phase 3: AI Content System
**Goal**: Intelligent daily content with historical events and future news curation

#### Phase 3A: Historical Events (Current Implementation)
**Status**: Implementing now
**Goal**: "Na ta dan v zgodovini" daily historical mountaineering events

##### Features to Implement
- [ ] Historical events database model
- [ ] DeepSeek LLM integration for content generation
- [ ] Daily automated content generation
- [ ] Homepage widget displaying today's event
- [ ] Historical events archive page
- [ ] Admin content management interface
- [ ] Manual refresh and regeneration capabilities

##### Database Models
```python
class HistoricalEvent(db.Model):
    id, date, year, title, description
    location, people, url, category
    created_at, is_featured
```

##### Implementation Steps
1. **Database Foundation**: Create models and migration
2. **LLM Service**: DeepSeek API integration with finalized prompt
3. **Content Generation**: Daily automation and admin controls
4. **Frontend Integration**: Homepage widget and archive page
5. **Admin Interface**: Content management and moderation
6. **Production Features**: Scheduling, monitoring, error handling

##### Phase 3A Definition of Done
- Daily historical events auto-generate reliably
- Homepage displays today's event beautifully
- Archive allows browsing events by date
- Admin can manage and refresh content
- Error handling with fallback content works

#### Phase 3A.1: Historical Events Data Quality (February 2026)
**Status**: Planned
**Goal**: Fix data quality issues, improve reliability, upgrade LLM providers

##### Change 1: Structured Date Storage
**Problem**: Dates stored as free-form strings in mixed formats — Slovenian ("Julij 15"), English ("09 November"), inconsistent day padding. Lookups for today's event fail when formats don't match.

**Solution**: Replace string `date` column with structured integer fields.
- Add `event_month` (Integer, 1-12) and `event_day` (Integer, 1-31) columns
- Keep `date` column temporarily for migration, then drop or keep as display cache
- Update `get_event_for_date()` / `get_todays_event()` to use `WHERE event_month=X AND event_day=Y`
- Migration script: parse existing `date` strings → populate `event_month`, `event_day`
- Display: Jinja2 filter or model property for Slovenian output ("16. februar")

**Files**: `models/content.py`, migration script, templates

**Tests**:
- Model storage and retrieval by month/day integers
- `get_todays_event()` lookup using int fields
- Slovenian display formatting
- Migration script correctly parses all existing date formats

##### Change 2: Prioritize Curated Over AI Events
**Problem**: `get_todays_event()` returns first match — could return AI-generated event even when a curated (scraped) event exists for the same date.

**Solution**: Update `get_event_for_date()` in `models/content.py` to `order_by(is_generated.asc())`. Curated events (False=0) sort before AI (True=1).

**Files**: `models/content.py`

**Tests**:
- Insert curated + AI event for same date, verify curated returned first

##### Change 3: Rewrite LLM Prompt
**Problem**: Current prompt asks LLM to provide URLs (biggest hallucination source). Allows vague multi-day events (step 3a). No confidence indicator for filtering unreliable results.

**Solution**:
- Remove: URL generation (steps 5a-5e, url_1, url_2), step 3a (multi-day events), url_methodology field
- Add: `"confidence": "high"|"medium"|"low"` field
- Add: Explicit constraint — "Only return events you are highly confident occurred on this exact date"
- Simplify: Focus on well-documented events (Everest, K2, major Alps ascents, famous tragedies)

**Files**: `utils/history_prompt.md`

**Tests**:
- Validate expected JSON structure from prompt (mock LLM response)

##### Change 4: Update Content Generation Logic
**Problem**: No distinction between curated/AI when serving events. No way to skip unreliable AI output.

**Solution**:
- `get_or_create_todays_event()`: check curated first → existing AI → generate new
- If LLM returns `confidence: "low"` → don't save, return None
- Mark saved AI events with `is_generated=True`
- Remove URL processing from `llm_service.py` (url_1, url_2, url_methodology)

**Files**: `utils/content_generation.py`, `utils/llm_service.py`

**Tests**:
- Mock LLM returning `confidence: "low"` → verify event not saved
- Mock LLM returning `confidence: "high"` → verify event saved
- Curated-first lookup logic

##### Change 5: Upgrade LLM Providers
**Problem**: Moonshot uses outdated `kimi-k2-0711-preview`. No Anthropic provider. Provider priority is not use-case-dependent.

**Solution**:
- Moonshot: `kimi-k2-0711-preview` → `kimi-k2.5`
- DeepSeek: keep `deepseek-chat`
- Add `AnthropicProvider` for `claude-sonnet-4-5`
- Add `ANTHROPIC_API_KEY` to `config.py` and `.env.example`
- Use-case-dependent provider priority in `ProviderManager`

**Provider priority by use case**:

| Priority | Historical events | Everything else |
|----------|-------------------|-----------------|
| 1st      | Claude Sonnet 4.5 | Kimi K2.5       |
| 2nd      | Kimi K2.5         | DeepSeek        |
| 3rd      | DeepSeek          | Claude Sonnet 4.5 |

**Files**: `utils/llm_providers.py`, `config.py`, `.env.example`

**Tests**:
- Anthropic provider initialization and connection test
- Provider fallback order for `historical` vs `other` use cases
- Fallback works when a provider is unavailable

##### Documentation Updates
- `docs/specification.md` — add LLM providers section with priority table
- `.env.example` — add `ANTHROPIC_API_KEY`, `MOONSHOT_API_KEY`, `DEEPSEEK_API_KEY`
- `CLAUDE.md` — update env vars reference

##### Execution Order
1. Change 1 (structured dates) — foundation, everything else depends on lookups
2. Change 2 (curated priority) — quick win, one line
3. Change 5 (providers) — needed before prompt changes
4. Change 3 (prompt rewrite)
5. Change 4 (generation logic) — ties it all together

---

#### Phase 3B: News Curation (Future Implementation)
**Status**: Architecture ready, implementation pending
**Goal**: Daily curation of 5 relevant mountaineering news items

##### Features to Implement (Future)
- [ ] News aggregation from NewsAPI and RSS feeds
- [ ] AI-powered relevance filtering and summarization
- [ ] Multiple daily news items with categories
- [ ] News archive with expiration management
- [ ] Real-time news source integration

##### Database Models (Designed, Not Implemented)
```python
class NewsItem(db.Model):
    id, title, summary, category, url
    relevance_score, news_date, created_at
    expires_at, is_featured
```

##### Architecture Decisions
- **Unified LLM Service**: Single service handles both content types
- **Separate Tables**: Different lifecycles require separate schemas
- **Shared Admin Interface**: Extensible design for both features
- **Cost-Effective Processing**: DeepSeek API (~$1-3/month)
- **Two-Stage Pipeline**: News aggregation → AI curation

##### Phase 3B Future Activation
- Enable news model usage
- Activate NewsAPI integration
- Populate admin interface
- Enable homepage news widget

---

## Technical Implementation Guidelines

### Code Organization
```
pd-triglav/
├── app.py                 # Application factory
├── config.py             # Configuration classes
├── requirements.txt      # Dependencies
├── .env                  # Environment variables (not in git)
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── trip.py
│   └── content.py
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── trips.py
│   ├── reports.py
│   └── admin.py
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── trips/
│   └── reports/
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

### Database Migration Strategy
- Use Flask-Migrate for all schema changes
- Create migration for each phase
- Include seed data in migrations when appropriate
- Test migrations on development data

### Testing Strategy
- **Unit Tests**: Models, utility functions
- **Integration Tests**: Authentication flows, trip workflows
- **Functional Tests**: End-to-end user journeys
- **API Tests**: AJAX endpoints and integrations

### Development Workflow
1. **Feature Branch**: Create branch for each feature
2. **Development**: Implement with tests
3. **Local Testing**: Verify functionality locally
4. **User Validation**: Demo to stakeholder
5. **Code Review**: Review implementation
6. **Merge**: Integrate to main branch
7. **Deploy**: Update staging/production

## Quality Assurance

### Code Quality Standards
- **PEP 8**: Python style guidelines
- **Type Hints**: Where beneficial for clarity
- **Docstrings**: For complex functions and classes
- **Error Handling**: Proper exception handling
- **Security**: Input validation, CSRF protection

### Performance Considerations
- **Database Indexing**: On frequently queried fields
- **Image Optimization**: Thumbnail generation, compression
- **Caching**: For static content and repeated queries
- **Pagination**: For large result sets

### Security Checklist
- Environment variables for all secrets
- SQL injection prevention (SQLAlchemy ORM)
- CSRF protection on forms
- Secure file upload validation
- Session security configuration
- Input sanitization and validation

## Deployment Strategy

### Development Environment
```bash
# Setup commands
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
python scripts/seed_db.py
flask run
```

### Production Deployment (Render)
- **Database**: Render managed PostgreSQL
- **File Storage**: AWS S3 bucket
- **Environment**: Production environment variables
- **Monitoring**: Basic application monitoring
- **Backups**: Database backup strategy

## Risk Mitigation

### Technical Risks
- **AWS S3 Costs**: Monitor usage, implement file size limits
- **LLM API Costs**: Rate limiting, caching, error handling
- **Database Performance**: Indexing strategy, query optimization
- **Photo Storage**: Compression, cleanup of unused files

### User Experience Risks
- **Approval Workflow**: Clear communication about pending status
- **Photo Upload**: Progress indication, error handling
- **Mobile Experience**: Responsive design testing
- **Slovenian Content**: Proper UTF-8 handling, localization

## Success Metrics by Phase

### Phase 1 Metrics
- User registration success rate > 95%
- Admin approval workflow < 24h average
- Authentication errors < 1%

### Phase 2 Metrics
- Trip signup success rate > 98%
- Email delivery rate > 95%
- Calendar load time < 2 seconds

### Phase 2E Metrics (Photos - Completed)
- Photo upload success rate > 90%
- Photo mosaic layouts display correctly across devices
- Upload size limits handle multiple large photos

### Phase 3 Metrics (AI Content)
- Daily historical events generation reliability > 99%
- Homepage widget load time < 2 seconds
- Admin content management response time < 1 second
- User engagement with historical content
- LLM API cost efficiency (target: <$5/month)

## Future Considerations

### Scalability Planning
- Database connection pooling
- CDN for static assets
- Load balancing considerations
- Monitoring and alerting

### Feature Extensions
- Mobile application development
- Integration with other club systems
- Advanced trip planning tools
- Member communication features

### Maintenance Planning
- Regular dependency updates
- Security patch management
- Data backup and recovery procedures
- Performance monitoring and optimization