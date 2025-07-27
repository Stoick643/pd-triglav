# PD Triglav Mountaineering Club - Project Specification

## Project Overview

Web application for PD Triglav mountaineering club that can be adapted for other clubs and associations. The application will be developed in Slovenian language and deployed on Render platform with source code hosted on GitHub.

## Target Users

**Primary:** Members of PD Triglav mountaineering club (~200 members)
**Secondary:** Other mountaineering clubs and outdoor associations

## User Roles & Permissions

### 1. Pending Member
- Limited access until admin approval
- Can view: Home page, basic club information
- Cannot: Access member features, view trips, create content

### 2. Member (Approved)
- Full access to club features
- Can view: All trips, reports, calendar, member content
- Can create: Trip reports, comments on reports/photos
- Can signup: For announced trips with automatic waitlist

### 3. Trip Leader
- All member permissions plus:
- Can create: Trip announcements
- Can manage: Their own trips and participants
- Can moderate: Comments on their trips

### 4. Admin
- Full system access
- Can manage: User accounts, approvals, roles
- Can moderate: All content across the platform
- Can access: Admin dashboard and system settings

## Core Features

### 1. Home Page & Club Information
- Club overview and basic information
- Recent activity summary
- Navigation for different user roles

### 2. Authentication System
- **Classical registration**: Email/password with admin approval
- **Google OAuth**: Social login with admin approval
- **Session management**: Secure login sessions
- **Role-based access**: Different permissions per role

### 3. Trip Management
- **Trip announcements**: Create, edit, view upcoming trips
- **Trip signup system**: Instant signup with automatic waitlists
- **Trip capacity**: No fixed limits (flexible based on trip type)
- **Email notifications**: Automatic notifications for new trips
- **Trip details**: Difficulty level, equipment, meeting points, costs

### 4. Trip Reports & Content
- **Rich text editor**: TinyMCE for formatted trip reports
- **Photo upload**: AWS S3 integration with thumbnail generation
- **Photo galleries**: Organized display of trip photos
- **Comments system**: Facebook-style commenting on reports and photos
- **Photo tagging**: Members can tag each other in photos

### 5. Calendar System
- **Upcoming events**: Visual calendar of announced trips
- **Past events**: Historical view of completed trips
- **Club events**: Non-trip club activities and meetings

### 6. AI Content System
- **"Na ta dan v zgodovini"**: Daily historical mountaineering events for current date
  - Significant mountaineering events (first ascents, tragedies, discoveries, achievements)
  - Detailed descriptions with people, locations, and significance
  - Archive page for browsing events by date
  - Homepage widget displaying today's event
- **Mountaineering News** (Future Phase):
  - Daily curation of 5 relevant mountaineering news items
  - Real-time news aggregation from multiple sources
  - AI-powered relevance filtering and summarization
  - Categories: safety, conditions, achievements, gear, events
- **Content Management**:
  - Automated daily generation using DeepSeek LLM API
  - Admin manual refresh and regeneration capabilities
  - Content editing and moderation tools
  - Error handling with fallback content

### 7. Email System
- **Trip notifications**: New trip announcements
- **Approval notifications**: Account approval status
- **System notifications**: Important club announcements

## Technical Architecture

### Backend Technology Stack
- **Framework**: Python Flask with blueprints
- **Database**: PostgreSQL (production), SQLite (development)
- **ORM**: SQLAlchemy with Flask-Migrate
- **Authentication**: Flask-Login + Authlib (OAuth)
- **Forms**: Flask-WTF with CSRF protection
- **Email**: Flask-Mail with threading support

### Frontend Technology Stack
- **Templates**: Jinja2 (built into Flask)
- **CSS Framework**: Bootstrap 5 for responsive design
- **JavaScript**: HTMX for dynamic interactions
- **Rich Text**: TinyMCE for trip report editing
- **Design**: Web-first with mobile support

### External Services
- **File Storage**: AWS S3 for photo storage
- **Image Processing**: Pillow for thumbnails and optimization
- **OAuth Provider**: Google OAuth 2.0
- **Email Service**: Render SMTP (free tier)
- **LLM API**: DeepSeek API for AI content generation
- **News Sources** (Future): NewsAPI, RSS feeds for news aggregation

### Development Environment
- **Virtual Environment**: Python venv
- **Environment Variables**: .env file for secrets
- **Development Server**: Flask development server
- **Database Migrations**: Flask-Migrate

## Database Schema Overview

### Users Table
- ID, email, password_hash, name
- Role (pending, member, trip_leader, admin)
- Approval status, created_at, last_login
- Google OAuth ID (optional)

### Trips Table
- ID, title, description, date, difficulty
- Created by (trip leader), capacity info
- Status (announced, completed, cancelled)

### Trip Reports Table
- ID, trip_id, author_id, title, content
- Photos, created_at, updated_at

### Comments Table
- ID, content_type (trip_report, photo)
- Content_id, author_id, content, created_at

### Photos Table
- ID, trip_report_id, filename, s3_key
- Caption, uploaded_by, created_at

### Historical Events Table
- ID, date, year, title, description
- Location, people, url, category
- Created_at, is_featured

### News Items Table (Future)
- ID, title, summary, category, url
- Relevance_score, news_date, created_at
- Expires_at, is_featured

## Deployment Strategy

### Development Environment
- Local PostgreSQL or SQLite database
- Local file storage for development
- Environment variables in .env file
- Flask development server

### Production Environment
- **Platform**: Render
- **Database**: Render managed PostgreSQL
- **File Storage**: AWS S3
- **Domain**: Initially Render subdomain, later custom domain
- **HTTPS**: Automatic SSL certificates

## Security Requirements

### Data Protection
- Environment variables for all secrets
- CSRF protection on all forms
- Secure password hashing
- SQL injection prevention (SQLAlchemy ORM)

### File Upload Security
- Image validation and processing
- File type restrictions
- Size limits for uploads
- Secure S3 bucket configuration

### Session Security
- Secure session cookies
- Session timeout handling
- Role-based access control

## Testing Strategy

### Test Data
- Seed script with test users:
  - admin@pd-triglav.si (Admin)
  - clan@pd-triglav.si (Member)
  - vodnik@pd-triglav.si (Trip Leader)
  - pending@pd-triglav.si (Pending Member)

### Test Coverage
- Unit tests for models and core functions
- Integration tests for authentication flow
- Functional tests for key user journeys
- Target: ~70% coverage on core functionality

## Documentation Requirements

- **README.md**: Setup and basic usage
- **docs/specification.md**: This document
- **docs/development-plan.md**: Implementation phases
- **CLAUDE.md**: Development context and commands
- **API documentation**: Key routes and functions
- **User guide**: For admins and members
- **Deployment guide**: Render setup instructions

## Success Metrics

### Phase 1 Success
- User registration and approval workflow functional
- Basic authentication (classical + OAuth) working
- Admin can approve/reject members
- Role-based access control implemented

### Phase 2 Success
- Trip announcements and signup system working
- Calendar view displaying events correctly
- Email notifications being sent
- Trip leaders can manage their trips

### Phase 3 Success
- Trip reports with photos can be created
- AWS S3 integration working
- Comments system functional
- Photo galleries displaying correctly

### Phase 4 Success
- LLM integration providing daily content
- Search functionality across content
- Admin dashboard fully functional
- Performance acceptable for 200+ users

## Future Enhancements (Post-MVP)

- Member profiles with climbing history
- Route database and conditions
- Gear exchange marketplace
- Achievement system and badges
- Mobile app (React Native/Flutter)
- Integration with weather APIs
- Advanced trip planning tools
- Multi-language support
- Federation with other clubs