# PD Triglav - Development Implementation Plan

## Development Philosophy

This plan serves as a **flexible guideline** rather than rigid requirements. Phases can be adjusted based on user feedback, technical discoveries, and changing priorities. The focus is on delivering working features incrementally while maintaining code quality and documentation.

---

## Completed Phases

### Phase 1: Core Authentication & User Management ✅
- Flask application structure with blueprints
- User model with roles (pending, member, trip_leader, admin)
- Classical registration (email/password) + Google OAuth
- Admin approval workflow
- Session management with Flask-Login
- Role-based access control
- Basic responsive layout with Bootstrap 5

### Phase 2: Trip Management & Calendar ✅
- Trip model and CRUD operations
- Trip announcements (create, edit, view)
- Trip signup system with waitlists
- Calendar view (upcoming and past trips)
- Email notifications for new trips (Amazon SES)
- Trip leader permissions and management
- Trip details (difficulty, equipment, cost, etc.)

### Phase 2B: Professional Design Transformation ✅
- Triglav Insurance corporate design identity
- Professional vertical sidebar navigation
- Dark gray primary (#2B2B2B) with red accent (#E31E24)
- Responsive mobile and desktop layouts
- Hero landing page with seasonal images, parallax, user-state CTAs

### Phase 2C: Modal System ✅
- Confirmation modals for critical actions (delete, logout)
- Trip signup/withdrawal modals
- Image lightbox for photo galleries
- Responsive modal behavior across devices

### Phase 3A: Historical Events ✅
- HistoricalEvent model with structured dates (event_month, event_day integers)
- 52 curated events imported from zsa.si
- Multi-provider LLM generation (Anthropic, Moonshot, DeepSeek)
- Homepage widget with Slovenian date display
- Admin regeneration controls
- Historical events archive with load-more
- Event detail pages

### Phase 3A.1: Historical Events Data Quality ✅ (February 2026)
**Changes implemented:**

1. **Structured Date Storage**: Replaced string `date` column with `event_month`/`event_day` integers. Eliminated format mismatch bugs permanently. Slovenian display via model properties (`date_sl`, `full_date_string`).

2. **Curated Events Priority**: `order_by(is_generated.asc())` ensures scraped events (52 curated) always display before AI-generated ones.

3. **Rewritten LLM Prompt**: Removed URL generation (biggest hallucination source). Added confidence field. All output in Slovenian. Stricter constraints on date accuracy.

4. **Confidence Filtering**: LLM returns `confidence: "high"|"medium"|"low"`. Low confidence triggers retry with fallback providers. If all providers return low, creates a fallback event.

5. **LLM Provider Upgrade**:
   - Added `AnthropicProvider` for Claude Sonnet 4.5
   - Upgraded Moonshot to Kimi K2.5 (temperature=1 required)
   - Use-case-dependent provider priority
   - Historical: Claude > Kimi > DeepSeek
   - Everything else: Kimi > DeepSeek > Claude

### Phase 3B: Daily News ✅
- RSS feed aggregation from multiple sources
- Slovenian sources: PZS (Planinska zveza Slovenije), Gore & Ljudje
- International sources: PlanetMountain, Gripped, UKClimbing, 8a.nu
- NewsAPI fallback for additional coverage
- Relevancy scoring with Slovenian content boost (+4.0)
- Web scraping from climbing-specific sites
- Homepage widget with article display
- Admin refresh controls

### Lazy Background Generation ✅ (February 2026)
- Background threads generate content on first visit (no blocking)
- JS polls `/api/todays-event` and `/api/daily-news` every 5 seconds
- Each section stops polling independently when ready
- 2-minute timeout with graceful "ni na voljo" fallback
- Solves free-tier scheduler issue (machine sleeps, 6 AM tasks don't fire)

---

## Future Phases

### Phase 4: Trip Reports & Photo System
**Status**: Not started
**Goal**: Content creation with rich trip reports and photo management

- Trip reports with rich text editor (TinyMCE)
- AWS S3 photo upload and management
- Image processing (thumbnails, compression with Pillow)
- Photo galleries and lightbox display
- Comments system on reports and photos
- Content moderation capabilities

### Phase 5: Advanced AI Features
**Status**: Not started
**Goal**: Intelligent content features beyond daily generation

- Intelligent search functionality
- Content recommendations based on user activity
- Trip difficulty analysis from descriptions
- Automatic trip report summaries

### Phase 6: Performance & Polish
**Status**: Ongoing
**Goal**: Production-ready performance and accessibility

- Caching for static content and repeated queries
- CDN for static assets
- Image optimization (WebP, responsive sizes)
- Advanced accessibility (screen readers, keyboard navigation)
- Cross-browser compatibility testing
- Mobile-first responsive improvements
- Monitoring and alerting

---

## Technical Guidelines

### Database Strategy
- SQLite for both development and production
- `db.create_all()` on startup (doesn't alter existing tables)
- For schema changes: drop table + restart (or migration script)
- No Flask-Migrate in production

### Testing Strategy
- **Unit Tests**: Models, utility functions
- **Integration Tests**: Authentication flows, database operations
- **Functional Tests**: End-to-end user workflows
- **API Tests**: AJAX endpoints and external integrations
- Target: ~70% coverage on core functionality
- 60 tests for historical events system

### LLM Cost Management
- Curated content prioritized (no API cost)
- Low-confidence results filtered (avoid saving garbage)
- Provider fallback chain minimizes failed requests
- Background generation (not blocking user requests)
- Target: <$5/month across all providers

### Security
- Environment variables for all secrets
- CSRF protection (Flask-WTF)
- SQL injection prevention (SQLAlchemy ORM)
- Secure password hashing (scrypt)
- File upload validation
- Session security configuration

---

*Last updated: February 2026*
