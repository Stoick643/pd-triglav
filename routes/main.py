import threading

from flask import (
    Blueprint,
    render_template,
    current_app,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
)
from flask_login import current_user, login_required

bp = Blueprint("main", __name__)

# Track active background generation to avoid duplicate threads
_generating_event = False
_generating_news = False


def _trigger_background_event_generation():
    """Start background thread to generate today's historical event"""
    global _generating_event
    if _generating_event:
        return  # Already generating

    _generating_event = True
    app = current_app._get_current_object()

    def generate():
        global _generating_event
        try:
            with app.app_context():
                from utils.content_generation import generate_todays_historical_event
                app.logger.info("Background: generating today's historical event...")
                event = generate_todays_historical_event()
                if event:
                    app.logger.info(f"Background: generated event: {event.title}")
                else:
                    app.logger.warning("Background: failed to generate historical event")
        except Exception as e:
            app.logger.error(f"Background event generation error: {e}")
        finally:
            _generating_event = False

    thread = threading.Thread(target=generate, daemon=True)
    thread.start()


def _trigger_background_news_fetch():
    """Start background thread to fetch daily news"""
    global _generating_news
    if _generating_news:
        return  # Already fetching

    _generating_news = True
    app = current_app._get_current_object()

    def fetch():
        global _generating_news
        try:
            with app.app_context():
                from utils.daily_news import fetch_and_cache_news
                app.logger.info("Background: fetching daily news...")
                articles = fetch_and_cache_news()
                app.logger.info(f"Background: cached {len(articles)} news articles")
        except Exception as e:
            app.logger.error(f"Background news fetch error: {e}")
        finally:
            _generating_news = False

    thread = threading.Thread(target=fetch, daemon=True)
    thread.start()


@bp.route("/health")
def health_check():
    """Health check endpoint for Fly.io monitoring"""
    return {"status": "healthy"}, 200


@bp.route("/")
def index():
    """Home page with hero landing page and role-based content"""
    todays_event = None
    recent_events = []
    daily_news = []
    upcoming_trips = []

    # Import hero utilities
    from utils.hero_utils import (
        get_user_specific_messaging,
        get_club_stats,
        get_hero_image_for_season,
    )

    # Get hero data
    hero_messaging = get_user_specific_messaging(current_user)
    club_stats = get_club_stats()
    hero_image = get_hero_image_for_season()

    # Get upcoming trips for authenticated users
    if current_user.is_authenticated and current_user.can_access_content():
        from models.trip import Trip, TripStatus
        from datetime import date

        upcoming_trips = (
            Trip.query
            .filter(Trip.trip_date >= date.today())
            .filter(Trip.status == TripStatus.ANNOUNCED)
            .order_by(Trip.trip_date.asc())
            .limit(5)
            .all()
        )

    # Get today's historical event (temporarily for everyone)
    if True:  # Temporarily show to everyone
        try:
            from datetime import datetime
            from models.content import HistoricalEvent
            from models.user import db
            import random

            now = datetime.now()

            # Get all events for today's date and pick a random one
            all_todays_events = HistoricalEvent.get_all_events_for_date(
                now.month, now.day
            )
            if all_todays_events:
                todays_event = random.choice(all_todays_events)
            else:
                todays_event = None

            # If no event exists, trigger background generation
            if not todays_event:
                _trigger_background_event_generation()

            # Get recent historical events (last 7, excluding today's)

            recent_events = (
                HistoricalEvent.query.filter(
                    db.not_(
                        db.and_(
                            HistoricalEvent.event_month == now.month,
                            HistoricalEvent.event_day == now.day,
                        )
                    )
                )
                .order_by(HistoricalEvent.created_at.desc())
                .limit(7)
                .all()
            )

        except Exception as e:
            current_app.logger.error(f"Failed to get historical events: {e}")
            # Continue without historical events

    # Get daily climbing news (from cache or API fallback)
    try:
        from models.user import db
        from utils.daily_news import get_daily_mountaineering_news_for_homepage

        # Ensure clean transaction state before attempting to get news
        db.session.rollback()

        daily_news = get_daily_mountaineering_news_for_homepage()
        if not daily_news:
            current_app.logger.info("No cached news found, triggering background fetch")
            _trigger_background_news_fetch()
    except Exception as e:
        # Rollback again to ensure clean state
        try:
            db.session.rollback()
        except:
            pass
        current_app.logger.error(f"Failed to get daily news: {e}")
        daily_news = []

    return render_template(
        "index.html",
        todays_event=todays_event,
        recent_events=recent_events,
        daily_news=daily_news,
        upcoming_trips=upcoming_trips,
        hero_messaging=hero_messaging,
        club_stats=club_stats,
        hero_image=hero_image,
    )


@bp.route("/history/event/<int:event_id>")
def historical_event_detail(event_id):
    """Display full details of a historical event"""
    try:
        from models.content import HistoricalEvent

        event = HistoricalEvent.query.get_or_404(event_id)
        return render_template("history/event_detail.html", event=event)
    except Exception as e:
        current_app.logger.error(f"Error loading historical event {event_id}: {e}")
        flash("Dogodek ni bil najden.", "error")
        return redirect(url_for("main.index"))


@bp.route("/about")
def about():
    """About page with club information"""
    return render_template("about.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    """Member dashboard - requires authentication"""
    if current_user.is_pending():
        return render_template("pending_approval.html")

    # Get upcoming trips for authenticated members
    from models.trip import Trip, TripStatus
    from models.content import TripReport, Photo
    from datetime import date

    upcoming_trips = (
        Trip.query
        .filter(Trip.trip_date >= date.today())
        .filter(Trip.status == TripStatus.ANNOUNCED)
        .order_by(Trip.trip_date.asc())
        .limit(5)
        .all()
    )

    # Get user's reports
    my_reports = (
        TripReport.query
        .filter_by(author_id=current_user.id)
        .order_by(TripReport.created_at.desc())
        .limit(5)
        .all()
    )

    # Get latest photos across all published reports
    recent_photos = (
        Photo.query
        .join(TripReport)
        .filter(TripReport.is_published == True)
        .order_by(Photo.created_at.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "dashboard.html",
        upcoming_trips=upcoming_trips,
        my_reports=my_reports,
        recent_photos=recent_photos,
    )


@bp.route("/admin")
@login_required
def admin():
    """Admin dashboard - requires admin role"""
    if not current_user.is_admin():
        return render_template("errors/403.html"), 403

    from models.user import User, UserRole
    from forms.admin_forms import UserApprovalForm, UserRejectionForm

    pending_users = User.get_pending_users()

    # Create forms for each pending user
    approval_forms = {}
    rejection_forms = {}

    for user in pending_users:
        approval_form = UserApprovalForm()
        approval_forms[user.id] = approval_form

        rejection_form = UserRejectionForm()
        rejection_forms[user.id] = rejection_form

    # Gather statistics
    from models.trip import Trip, TripStatus
    from models.content import TripReport, Photo
    from datetime import date

    all_users = User.query.all()
    total_users = len(all_users)
    active_users = len([u for u in all_users if u.role.value != 'pending'])
    total_trips = Trip.query.count()
    upcoming_trips = Trip.query.filter(Trip.trip_date >= date.today()).count()
    total_reports = TripReport.query.count()
    published_reports = TripReport.query.filter_by(is_published=True).count()
    total_photos = Photo.query.count()

    # Get all registered users for user management
    registered_users = (
        User.query
        .filter(User.role != UserRole.PENDING)
        .order_by(User.name.asc())
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        pending_users=pending_users,
        approval_forms=approval_forms,
        rejection_forms=rejection_forms,
        total_users=total_users,
        active_users=active_users,
        total_trips=total_trips,
        upcoming_trips=upcoming_trips,
        total_reports=total_reports,
        published_reports=published_reports,
        total_photos=total_photos,
        registered_users=registered_users,
    )


@bp.route("/admin/approve-user/<int:user_id>", methods=["POST"])
@login_required
def approve_user(user_id):
    """Approve pending user - admin only"""
    if not current_user.is_admin():
        flash("Dostop zavrnjen.", "error")
        return redirect(url_for("main.index"))

    from models.user import db, User, UserRole
    from forms.admin_forms import UserApprovalForm

    form = UserApprovalForm()

    current_app.logger.warn(f"Approval form submitted for user {user_id}")
    current_app.logger.warn(f"Form data: {dict(request.form)}")
    current_app.logger.warn(f"Form validation result: {form.validate_on_submit()}")
    current_app.logger.warn(f"Form errors: {form.errors}")

    if not form.validate_on_submit():
        flash("Neveljaven zahtevek za odobritev.", "error")
        current_app.logger.error(f"Form validation failed: {form.errors}")
        return redirect(url_for("main.admin"))

    user = User.query.get_or_404(user_id)

    if user.role != UserRole.PENDING:
        flash("Uporabnik ni na čakanju za odobritev.", "warning")
        return redirect(url_for("main.admin"))

    try:
        user.role = UserRole.MEMBER
        user.is_approved = True
        db.session.commit()

        # Send welcome email to approved user
        try:
            from utils.email_service import send_email
            send_email(
                subject="PD Triglav - Vaša registracija je odobrena!",
                recipient=user.email,
                template_html="emails/user_approved.html",
                template_txt="emails/user_approved.txt",
                user=user,
            )
            current_app.logger.info(f"Approval email sent to {user.email}")
        except Exception as mail_err:
            current_app.logger.warning(f"Failed to send approval email to {user.email}: {mail_err}")

        flash(f"Uporabnik {user.name} je bil uspešno odobren kot član.", "success")
        current_app.logger.info(f"Admin {current_user.email} approved user {user.email}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to approve user {user.email}: {e}")
        flash(f"Napaka pri odobritvi uporabnika: {str(e)}", "error")

    return redirect(url_for("main.admin"))


@bp.route("/admin/reject-user/<int:user_id>", methods=["POST"])
@login_required
def reject_user(user_id):
    """Reject pending user - admin only"""
    if not current_user.is_admin():
        flash("Dostop zavrnjen.", "error")
        return redirect(url_for("main.index"))

    from models.user import db, User, UserRole
    from forms.admin_forms import UserRejectionForm

    form = UserRejectionForm()

    current_app.logger.info(f"Rejection form submitted for user {user_id}")
    current_app.logger.info(f"Form data: {dict(request.form)}")
    current_app.logger.info(f"Form validation result: {form.validate_on_submit()}")
    current_app.logger.info(f"Form errors: {form.errors}")

    if not form.validate_on_submit():
        flash("Neveljaven zahtevek za zavrnitev.", "error")
        current_app.logger.error(f"Form validation failed: {form.errors}")
        return redirect(url_for("main.admin"))

    user = User.query.get_or_404(user_id)

    if user.role != UserRole.PENDING:
        flash("Uporabnik ni na čakanju za odobritev.", "warning")
        return redirect(url_for("main.admin"))

    try:
        user_name = user.name
        user_email = user.email
        db.session.delete(user)
        db.session.commit()
        flash(f"Uporabnik {user_name} je bil zavrnjen in odstranjen.", "info")
        current_app.logger.info(
            f"Admin {current_user.email} rejected and deleted user {user_email}"
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to reject user {user.email}: {e}")
        flash(f"Napaka pri zavrnitvi uporabnika: {str(e)}", "error")

    return redirect(url_for("main.admin"))


@bp.route("/admin/regenerate-today-event", methods=["POST"])
@login_required
def regenerate_today_event():
    """Regenerate today's historical event - admin only"""
    if not current_user.is_admin():
        return jsonify({"error": "Dostop zavrnjen. Potrebne so administratorske pravice."}), 403

    try:
        from models.content import HistoricalEvent
        from utils.content_generation import HistoricalEventService
        from datetime import datetime

        # Find existing event for today
        now = datetime.now()
        existing_event = HistoricalEvent.get_event_for_date(now.month, now.day)

        if existing_event:
            # Regenerate existing event
            service = HistoricalEventService()
            updated_event = service.regenerate_event(existing_event.id)

            current_app.logger.info(
                f"Admin {current_user.email} regenerated event: {updated_event.title}"
            )

            return jsonify(
                {
                    "success": True,
                    "message": "Dogodek je bil uspešno regeneriran.",
                    "event": {
                        "id": updated_event.id,
                        "title": updated_event.title,
                        "description": updated_event.description,
                        "location": updated_event.location,
                        "people": updated_event.people_list,
                        "category": updated_event.category.value,
                        "full_date_string": updated_event.full_date_string,
                        "is_generated": updated_event.is_generated,
                    },
                }
            )
        else:
            # Generate new event for today
            service = HistoricalEventService()
            new_event = service.generate_daily_event()

            current_app.logger.info(
                f"Admin {current_user.email} generated new event: {new_event.title}"
            )

            return jsonify(
                {
                    "success": True,
                    "message": "Nov dogodek je bil uspešno ustvarjen.",
                    "event": {
                        "id": new_event.id,
                        "title": new_event.title,
                        "description": new_event.description,
                        "location": new_event.location,
                        "people": new_event.people_list,
                        "category": new_event.category.value,
                        "full_date_string": new_event.full_date_string,
                        "is_generated": new_event.is_generated,
                    },
                }
            )

    except Exception as e:
        current_app.logger.error(f"Error regenerating historical event: {e}")
        return (
            jsonify(
                {"success": False, "error": "Napaka pri regeneraciji dogodka. Poskusite ponovno."}
            ),
            500,
        )


@bp.route("/admin/refresh-news", methods=["POST"])
@login_required
def refresh_news():
    """Refresh daily news - admin only"""
    if not current_user.is_admin():
        return jsonify({"error": "Dostop zavrnjen. Potrebne so administratorske pravice."}), 403

    try:
        from models.content import DailyNews
        from utils.daily_news import fetch_and_cache_news
        from datetime import date

        # Clear today's cached news
        today = date.today()
        existing_news = DailyNews.query.filter_by(news_date=today).first()
        if existing_news:
            existing_news.articles = []
            existing_news.articles_count = 0

        # Fetch fresh news using improved RSS parser
        fresh_articles = fetch_and_cache_news()

        current_app.logger.info(
            f"Admin {current_user.email} refreshed news: {len(fresh_articles)} articles"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Novice so bile uspešno osvežene. Pridobljenih {len(fresh_articles)} člankov.",
                "articles_count": len(fresh_articles),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error refreshing news: {e}")
        return (
            jsonify({"success": False, "error": "Napaka pri osvežitvi novic. Poskusite ponovno."}),
            500,
        )


@bp.route("/admin/test-email", methods=["POST"])
@login_required
def test_email():
    """Send a test email to the current admin user"""
    if not current_user.is_admin():
        flash("Dostop zavrnjen.", "error")
        return redirect(url_for("main.index"))

    try:
        from utils.email_service import is_mail_configured, send_email

        if not is_mail_configured():
            flash("Email ni konfiguriran. Preverite MAIL_SERVER, MAIL_USERNAME in MAIL_PASSWORD v nastavitvah.", "warning")
            return redirect(url_for("main.admin"))

        thread = send_email(
            subject="PD Triglav - Testno sporočilo",
            recipient=current_user.email,
            template_html="emails/test_email.html",
            template_txt="emails/test_email.txt",
            user=current_user,
        )

        if thread:
            flash(f"Testno sporočilo poslano na {current_user.email}. Preverite nabiralnik.", "success")
        else:
            flash("Email ni bil poslan. Preverite konfiguracijo.", "warning")

    except Exception as e:
        current_app.logger.error(f"Test email error: {e}")
        flash(f"Napaka pri pošiljanju: {str(e)}", "error")

    return redirect(url_for("main.admin"))


@bp.route("/api/todays-event")
def api_todays_event():
    """Polling endpoint: returns today's historical event if available"""
    try:
        from models.content import HistoricalEvent

        event = HistoricalEvent.get_todays_event()
        if event:
            return jsonify({
                "ready": True,
                "event": {
                    "id": event.id,
                    "event_month": event.event_month,
                    "event_day": event.event_day,
                    "year": event.year,
                    "title": event.title,
                    "description": event.description,
                    "location": event.location,
                    "people": event.people_list or [],
                    "url": event.url,
                    "url_secondary": event.url_secondary,
                    "category": event.category.value,
                    "date_sl": event.date_sl,
                    "full_date_string": event.full_date_string,
                    "is_generated": event.is_generated,
                    "created_at": event.created_at.strftime("%d. %m. %Y") if event.created_at else "",
                },
            })
        else:
            return jsonify({"ready": False, "generating": _generating_event})
    except Exception as e:
        current_app.logger.error(f"Error in todays-event API: {e}")
        return jsonify({"ready": False, "error": str(e)}), 500


@bp.route("/api/daily-news")
def api_daily_news():
    """Polling endpoint: returns daily news if available"""
    try:
        from utils.daily_news import get_daily_mountaineering_news_for_homepage

        news = get_daily_mountaineering_news_for_homepage()
        if news:
            return jsonify({
                "ready": True,
                "articles": news,
            })
        else:
            return jsonify({"ready": False, "generating": _generating_news})
    except Exception as e:
        current_app.logger.error(f"Error in daily-news API: {e}")
        return jsonify({"ready": False, "error": str(e)}), 500


@bp.route("/api/history/recent")
def get_recent_historical_events():
    """Get recent historical events for archive display"""
    try:
        from models.content import HistoricalEvent

        # Get pagination parameters
        offset = request.args.get("offset", 0, type=int)
        limit = request.args.get("limit", 7, type=int)

        # Ensure reasonable limits
        limit = min(limit, 20)  # Max 20 events per request

        # Get recent events (excluding today's event to avoid duplication)
        from datetime import datetime
        from models.user import db

        now = datetime.now()

        exclude_today = db.not_(
            db.and_(
                HistoricalEvent.event_month == now.month,
                HistoricalEvent.event_day == now.day,
            )
        )

        events = (
            HistoricalEvent.query.filter(exclude_today)
            .order_by(HistoricalEvent.created_at.desc(), HistoricalEvent.year.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Convert to JSON format
        events_data = []
        for event in events:
            events_data.append(
                {
                    "id": event.id,
                    "event_month": event.event_month,
                    "event_day": event.event_day,
                    "year": event.year,
                    "title": event.title,
                    "description": (
                        event.description[:200] + "..."
                        if len(event.description) > 200
                        else event.description
                    ),
                    "location": event.location,
                    "people": event.people_list[:3] if event.people_list else [],
                    "category": event.category.value,
                    "full_date_string": event.full_date_string,
                    "is_featured": event.is_featured,
                }
            )

        # Check if there are more events
        total_events = HistoricalEvent.query.filter(exclude_today).count()
        has_more = (offset + limit) < total_events

        return jsonify(
            {
                "success": True,
                "events": events_data,
                "has_more": has_more,
                "total": total_events,
                "loaded": offset + len(events_data),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error fetching recent historical events: {e}")
        return (
            jsonify({"success": False, "error": "Napaka pri nalaganju zgodovinskih dogodkov."}),
            500,
        )


@bp.route("/api/historical-events")
def api_historical_events():
    """API endpoint for historical events by date"""
    try:
        from models.content import HistoricalEvent
        from datetime import datetime

        # Get date parameter (format: DD-MM or YYYY-MM-DD)
        date_param = request.args.get("date")
        limit = request.args.get("limit", 10, type=int)

        # Ensure reasonable limits
        limit = min(limit, 100)  # Max 100 events per request

        if not date_param:
            # If no date provided, use today's date
            now = datetime.now()
            search_month = now.month
            search_day = now.day
        elif "-" in date_param:
            # Format: DD-MM
            parts = date_param.split("-")
            search_day = int(parts[0])
            search_month = int(parts[1])
        else:
            # Try parsing as text format
            from utils.llm_service import parse_date_string
            search_month, search_day = parse_date_string(date_param)
            if search_month is None:
                return jsonify({"error": "Invalid date format. Use DD-MM."}), 400

        # Query events for the specific date
        events = (
            HistoricalEvent.query
            .filter_by(event_month=search_month, event_day=search_day)
            .order_by(HistoricalEvent.is_generated.asc(), HistoricalEvent.year.desc())
            .limit(limit)
            .all()
        )

        # Convert to JSON format
        events_data = []
        for event in events:
            events_data.append(
                {
                    "id": event.id,
                    "event_month": event.event_month,
                    "event_day": event.event_day,
                    "year": event.year,
                    "title": event.title,
                    "description": event.description,
                    "location": event.location,
                    "people": event.people_list if event.people_list else [],
                    "category": event.category.value,
                    "full_date_string": event.full_date_string,
                    "is_featured": event.is_featured,
                    "url": event.url,
                }
            )

        return jsonify(events_data)

    except ValueError:
        # Invalid date format
        return jsonify({"error": "Invalid date format. Use DD-MM or YYYY-MM-DD."}), 400

    except Exception as e:
        current_app.logger.error(f"Error fetching historical events: {e}")
        return jsonify({"error": "Server error while fetching events."}), 500
