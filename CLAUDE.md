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

# Seed development data (full test data)
python3 scripts/seed_db.py

# OR seed production data (admin only)
python3 scripts/seed_db_prod.py
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
├── pd_triglav.db        # Main development database
├── test.db             # Single reusable test database
├── .gitkeep            # Ensures directory is tracked
└── README.md           # Database documentation
```

### Database Isolation
- **Development**: `databases/pd_triglav.db` (persistent, contains seeded data)
- **Testing**: Hybrid strategy - `databases/test.db` (single mode) or `databases/test_gw*.db` (parallel mode)
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
│   ├── seed_db.py      # Development data seeding
│   └── seed_db_prod.py # Production data seeding (admin only)
└── docs/               # Documentation
```

## Development Workflow

### Phase 1: Authentication & User Management ✅ **COMPLETED**
- [x] Basic Flask app structure
- [x] User model with roles
- [x] Classical + Google OAuth registration
- [x] Admin approval workflow
- [x] Role-based access control

### Phase 2: Professional Design Transformation ✅ **COMPLETED**
- [x] Triglav Insurance corporate design identity adoption
- [x] Professional vertical sidebar navigation system
- [x] Dark gray primary (#2B2B2B) with red accent (#E31E24) color scheme
- [x] Responsive mobile and desktop layouts
- [x] Navigation stability fixes and optimization
- [x] Theme system removal for simplified corporate design
- [x] Color consistency throughout application

### Phase 3: Modal System Implementation **(NEXT)**
- [ ] Professional modal dialogs for forms and interactions
- [ ] Confirmation modals for critical actions (delete, logout, etc.)
- [ ] Image lightbox modals for photo galleries
- [ ] User profile and settings modal interactions
- [ ] Responsive modal behavior across devices
- [ ] Modal accessibility (keyboard navigation, focus management)

### Phase 4: Professional Polish **(UPCOMING)**
- [ ] Micro-interactions and smooth animations
- [ ] Advanced accessibility features (screen readers, keyboard navigation)
- [ ] Performance optimizations and loading states
- [ ] Final UX refinements and user testing feedback
- [ ] Cross-browser compatibility testing
- [ ] Mobile-first responsive design improvements

### Phase 5: Trip Management **(FUTURE)**
- [ ] Trip announcements and CRUD operations
- [ ] Calendar view implementation
- [ ] Trip signup system with waitlists
- [ ] Email notifications for trip updates

### Phase 6: Content & Photos **(FUTURE)**
- [ ] Trip reports with rich text editing
- [ ] AWS S3 photo upload and management
- [ ] Comments system for trips and reports
- [ ] Photo galleries with lightbox functionality

### Phase 7: AI Features **(FUTURE)**
- [ ] Historical events integration
- [ ] Mountaineering news summary
- [ ] Intelligent search functionality

## Hero Landing Page Implementation

### Overview
Transform the home page into a compelling hero landing page with stunning mountain photography, optimized messaging, and user-state-aware CTAs. Create an immersive first impression that converts visitors into members while showcasing the club's expertise and community.

### Strategic Decision: Home Page as Hero
**Why the home page (`/`) is the perfect hero location:**
- **Universal Landing Point** - All visitors (Google search, direct links, referrals) land here first
- **Content Visibility** - Historical events and news are already public, creating value for non-members
- **Conversion Funnel** - Perfect place to convert visitors → members
- **SEO Benefits** - Search engines will index this compelling content

### Files to Modify

#### Frontend Templates
- `templates/index.html` - Complete hero section redesign and content restructuring
- `templates/base.html` - Add hero-specific meta tags and preload directives

#### CSS Styling
- `static/css/app.css` - Add hero section styles, responsive design, animations
- `static/css/components.css` - Create reusable hero components and overlays
- `static/css/design-system.css` - Extend with hero-specific CSS variables

#### Backend Logic
- `routes/main.py` - Add hero image selection logic and user messaging
- `utils/hero_utils.py` - NEW: Hero image management and optimization utilities

#### Static Assets
- `static/images/hero/` - NEW: Organize and optimize hero images
- `static/js/hero.js` - NEW: Hero animations, parallax, lazy loading

### Function Specifications

#### Backend Functions (`utils/hero_utils.py`)
```python
def get_hero_image_for_season():
    """Returns seasonal and time-based hero image path with enhanced rotation system.
    
    Features:
    - Seasonal rotation (winter, spring, summer, autumn)
    - Time-based variations (dawn, day, dusk, night)
    - Intelligent fallback system
    - Seasonal daylight adjustments
    """

def get_time_period(hour, season):
    """Determines time period (dawn/day/dusk/night) based on hour and season.
    
    Time boundaries vary by season to match natural daylight patterns:
    - Winter: Dawn 5-9, Day 9-17, Dusk 17-22, Night 22-5
    - Spring: Dawn 5-9, Day 9-18, Dusk 18-22, Night 22-5  
    - Summer: Dawn 4-8, Day 8-19, Dusk 19-23, Night 23-4
    - Autumn: Dawn 6-9, Day 9-17, Dusk 17-21, Night 21-6
    """

def get_user_specific_messaging(user):  
    """Generates personalized hero headline and CTA text based on user authentication state."""

def optimize_hero_images():
    """Processes uploaded images into multiple sizes and WebP formats for performance."""
```

#### Frontend Functions (`static/js/hero.js`)
```javascript
function initHeroParallax():
    """Initializes smooth parallax scrolling effect for hero background image."""

function lazyLoadHeroImage():
    """Implements progressive image loading with blur-to-sharp transition effect."""

function animateHeroContent():
    """Handles entrance animations for hero text and CTA buttons on page load."""
```

#### CSS Classes (`static/css/app.css`)
```css
.hero-section:
    """Full-viewport hero container with background image and responsive behavior."""

.hero-overlay:
    """Dark gradient overlay ensuring text readability over any background image."""

.hero-content:
    """Centered content container with proper spacing and mobile optimization."""
```

### Test Specifications

#### Visual & Layout Tests
- `test_hero_renders_correctly` - Hero section displays with proper dimensions
- `test_hero_responsive_behavior` - Mobile and desktop layouts work correctly  
- `test_hero_image_loading` - Background images load and display properly
- `test_hero_overlay_readability` - Text remains readable over all images

#### User Experience Tests  
- `test_hero_messaging_by_user_state` - Different messages for logged/not logged users
- `test_hero_cta_buttons_functional` - All call-to-action buttons navigate correctly
- `test_hero_animations_smooth` - Entrance animations perform without lag
- `test_hero_accessibility_compliant` - Proper alt texts and keyboard navigation

#### Performance Tests
- `test_hero_image_optimization` - Images serve in optimal formats and sizes
- `test_hero_loading_speed` - Page loads within performance benchmarks
- `test_hero_lazy_loading` - Non-critical images load after hero content
- `test_hero_mobile_performance` - Mobile devices load quickly with data savings

#### Content Tests
- `test_hero_seasonal_images` - Different images display based on season/date
- `test_hero_messaging_localization` - All text displays in Slovenian correctly
- `test_hero_social_proof_display` - Member count and stats show accurately
- `test_hero_fallback_graceful` - Site works even if hero images fail

### Implementation Phases

#### Phase 1: Foundation (High Priority)
1. Reorganize and optimize hero images
2. Create basic hero HTML structure in index.html
3. Implement responsive CSS grid layout
4. Add user-state messaging logic

#### Phase 2: Enhancement (Medium Priority)  
1. Add parallax scrolling effects
2. Implement entrance animations
3. Create seasonal image rotation
4. Optimize for performance and accessibility

#### Phase 3: Polish (Lower Priority)
1. Add advanced lazy loading
2. Implement A/B testing for messaging
3. Add analytics tracking for CTAs  
4. Create admin interface for hero management

### Expected Outcomes
- **Conversion Rate**: 25-40% increase in registration clicks
- **Engagement**: 60%+ reduction in bounce rate
- **Performance**: <2s load time on mobile, >90 Lighthouse score
- **User Experience**: Immersive, professional first impression that builds trust and excitement

### Hero Content Strategy

#### Messaging Options (Choose Best)
- **Primary**: "Odkrijte Veličino Slovenskih Gora" (Discover the Majesty of Slovenian Mountains)
- **Alternative**: "Vaša Planinska Pustolovščina Se Začne Tukaj" (Your Mountain Adventure Starts Here)
- **Community-focused**: "Pridružite Se Skupnosti Gorskih Raziskovalcev" (Join the Community of Mountain Explorers)

#### Call-to-Action Buttons
- **Primary CTA**: "Začni Svojo Pustolovščino" (Start Your Adventure) → Register
- **Secondary CTA**: "Oglej Si Prihajajo Izlete" (View Upcoming Trips) → About/Content

#### User State-Specific Experience
- **Not logged in**: Adventure-focused registration messaging
- **Pending approval**: Encourage patience with club highlights and community showcase
- **Active member**: Personalized welcome with dashboard access and recent activity

#### Social Proof Elements
- "Pridružilo se nam je že 200+ planincev" (200+ mountaineers have joined us)
- "50+ izletov letno • Vsi nivoji • 15+ let izkušenj" (50+ trips yearly • All levels • 15+ years experience)
- Member testimonials and safety record highlights

### Image Asset Requirements

#### Enhanced Hero Image Organization (static/images/hero/)
**Time-Based Rotation System** - Images change based on both season and time of day:

**Base Seasonal Images (Required):**
- `hero-winter.jpg` (Dec-Feb, day)
- `hero-primary.jpg` (Mar-May, day) 
- `hero-summer.jpg` (Jun-Aug, day)
- `hero-secondary.jpg` (Sep-Nov, day)

**Time-Based Variations (Optional Enhancement):**
- `hero-winter-dawn.jpg`, `hero-winter-dusk.jpg`, `hero-winter-night.jpg`
- `hero-primary-dawn.jpg`, `hero-primary-dusk.jpg`, `hero-primary-night.jpg`
- `hero-summer-dawn.jpg`, `hero-summer-dusk.jpg`, `hero-summer-night.jpg`
- `hero-secondary-dawn.jpg`, `hero-secondary-dusk.jpg`, `hero-secondary-night.jpg`

**Intelligent Fallbacks:**
1. Time-specific image (e.g., `hero-summer-dawn.jpg`)
2. Base seasonal image (e.g., `hero-summer.jpg`)
3. Primary fallback (`hero-primary.jpg`)

**Time Boundaries (Seasonal Daylight Adjustment):**
- **Winter**: Dawn 5-9, Day 9-17, Dusk 17-22, Night 22-5
- **Spring**: Dawn 5-9, Day 9-18, Dusk 18-22, Night 22-5
- **Summer**: Dawn 4-8, Day 8-19, Dusk 19-23, Night 23-4
- **Autumn**: Dawn 6-9, Day 9-17, Dusk 17-21, Night 21-6

#### Optimization Needs
- Resize to multiple breakpoints (mobile, tablet, desktop)
- Convert to WebP format for modern browsers
- Create fallback JPEG versions
- Implement lazy loading for performance

## Common Issues & Solutions

### Database Issues
```bash
# Reset database (development only)
rm databases/pd_triglav.db  # Remove development database
flask db upgrade

# Reset test database
rm databases/test.db

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