"""Trip management routes for trip announcements"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime
from sqlalchemy import or_

from models.user import db, UserRole
from models.trip import Trip, TripDifficulty, TripStatus, TripParticipant, ParticipantStatus
from models.content import Comment, CommentType
from forms.trip_forms import TripForm, TripSignupForm, TripCommentForm, TripFilterForm

bp = Blueprint("trips", __name__)


def require_trip_leader(f):
    """Decorator to require trip leader or admin role"""

    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Prosim prijavite se za dostop do te strani.", "warning")
            return redirect(url_for("auth.login"))

        if current_user.role not in [UserRole.TRIP_LEADER, UserRole.ADMIN]:
            flash("Samo vodniki in administratorji lahko upravljajo izlete.", "error")
            return abort(403)

        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@bp.route("/")
def list_trips():
    """Display list of trip announcements with filtering"""
    form = TripFilterForm()

    # Base query for announced trips
    query = Trip.query

    # Apply filters if form is submitted
    if form.validate_on_submit():
        if form.difficulty.data:
            query = query.filter(Trip.difficulty == TripDifficulty(form.difficulty.data))

        if form.status.data:
            if form.status.data == "upcoming":
                query = query.filter(
                    Trip.trip_date >= date.today(), Trip.status == TripStatus.ANNOUNCED
                )
            elif form.status.data == "past":
                query = query.filter(Trip.trip_date < date.today())
            else:
                query = query.filter(Trip.status == TripStatus(form.status.data))

        if form.search.data:
            search_term = f"%{form.search.data}%"
            query = query.filter(
                or_(Trip.title.ilike(search_term), Trip.destination.ilike(search_term))
            )
    else:
        # Default: show upcoming announced trips
        query = query.filter(Trip.trip_date >= date.today(), Trip.status == TripStatus.ANNOUNCED)

    # Order by trip date
    trips = query.order_by(Trip.trip_date.asc()).all()

    return render_template("trips/list.html", trips=trips, form=form)


@bp.route("/<int:trip_id>")
def view_trip(trip_id):
    """Display individual trip announcement with comments"""
    trip = Trip.query.get_or_404(trip_id)

    # Get comments for this trip
    comments = Comment.get_comments_for_trip(trip_id)

    # Get user's participation status
    user_status = None
    if current_user.is_authenticated:
        user_status = trip.get_participant_status(current_user)

    # Forms for logged-in users
    signup_form = TripSignupForm() if current_user.is_authenticated else None
    comment_form = TripCommentForm() if current_user.is_authenticated else None

    return render_template(
        "trips/detail.html",
        trip=trip,
        comments=comments,
        user_status=user_status,
        signup_form=signup_form,
        comment_form=comment_form,
    )


@bp.route("/create", methods=["GET", "POST"])
@require_trip_leader
def create_trip():
    """Create new trip announcement"""
    form = TripForm()

    if form.validate_on_submit():
        # Determine trip status based on which button was clicked
        status = TripStatus.ANNOUNCED
        if "save_draft" in request.form:
            # For now, we'll just save as announced - draft functionality can be added later
            pass

        trip = Trip(
            title=form.title.data,
            description=form.description.data,
            destination=form.destination.data,
            trip_date=form.trip_date.data,
            meeting_time=form.meeting_time.data,
            meeting_point=form.meeting_point.data,
            return_time=form.return_time.data,
            difficulty=TripDifficulty(form.difficulty.data),
            max_participants=form.max_participants.data,
            equipment_needed=form.equipment_needed.data,
            cost_per_person=form.cost_per_person.data,
            status=status,
            leader_id=current_user.id,
        )

        try:
            db.session.add(trip)
            db.session.commit()

            flash(f'Izlet "{trip.title}" je bil uspešno objavljen!', "success")
            return redirect(url_for("trips.view_trip", trip_id=trip.id))

        except Exception:
            db.session.rollback()
            flash("Napaka pri shranjevanju izleta. Poskusite znova.", "error")

    return render_template("trips/create.html", form=form)


@bp.route("/<int:trip_id>/edit", methods=["GET", "POST"])
@require_trip_leader
def edit_trip(trip_id):
    """Edit existing trip announcement"""
    trip = Trip.query.get_or_404(trip_id)

    # Only trip leader or admin can edit
    if not (current_user.id == trip.leader_id or current_user.is_admin()):
        flash("Samo vodnik ali administrator lahko ureja ta izlet.", "error")
        return abort(403)

    form = TripForm(obj=trip)

    if form.validate_on_submit():
        # Update trip with form data
        form.populate_obj(trip)
        trip.difficulty = TripDifficulty(form.difficulty.data)
        trip.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            flash(f'Izlet "{trip.title}" je bil uspešno posodobljen!', "success")
            return redirect(url_for("trips.view_trip", trip_id=trip.id))

        except Exception:
            db.session.rollback()
            flash("Napaka pri posodabljanju izleta. Poskusite znova.", "error")

    return render_template("trips/edit.html", form=form, trip=trip)


@bp.route("/<int:trip_id>/cancel", methods=["POST"])
@require_trip_leader
def cancel_trip(trip_id):
    """Cancel trip announcement"""
    trip = Trip.query.get_or_404(trip_id)

    # Only trip leader or admin can cancel
    if not (current_user.id == trip.leader_id or current_user.is_admin()):
        flash("Samo vodnik ali administrator lahko odpove ta izlet.", "error")
        return abort(403)

    # Can't cancel past trips or already cancelled trips
    if trip.is_past:
        flash("Ne morete odpovedati preteklih izletov.", "error")
        return redirect(url_for("trips.view_trip", trip_id=trip.id))

    if trip.status == TripStatus.CANCELLED:
        flash("Ta izlet je že odpovedan.", "warning")
        return redirect(url_for("trips.view_trip", trip_id=trip.id))

    try:
        trip.status = TripStatus.CANCELLED
        db.session.commit()

        # TODO: Send email notifications to participants
        flash(f'Izlet "{trip.title}" je bil uspešno odpovedan.', "success")

    except Exception:
        db.session.rollback()
        flash("Napaka pri odpovedi izleta. Poskusite znova.", "error")

    return redirect(url_for("trips.view_trip", trip_id=trip.id))


@bp.route("/<int:trip_id>/signup", methods=["POST"])
@login_required
def signup_for_trip(trip_id):
    """Sign up for trip announcement"""
    trip = Trip.query.get_or_404(trip_id)
    form = TripSignupForm()

    if not form.validate_on_submit():
        flash("Napaka pri prijavi. Preverite vnešene podatke.", "error")
        return redirect(url_for("trips.view_trip", trip_id=trip_id))

    # Check if user can sign up
    if not trip.can_user_signup(current_user):
        flash("Na ta izlet se ne morete prijaviti.", "error")
        return redirect(url_for("trips.view_trip", trip_id=trip_id))

    try:
        participant = trip.add_participant(current_user)
        if participant:
            db.session.commit()

            if participant.status == ParticipantStatus.CONFIRMED:
                flash("Uspešno ste se prijavili na izlet!", "success")
            else:
                flash("Prijava je uspešna! Dodani ste na čakalno listo.", "info")
        else:
            flash("Napaka pri prijavi. Verjetno ste že prijavljeni.", "error")

    except Exception:
        db.session.rollback()
        flash("Napaka pri prijavi na izlet. Poskusite znova.", "error")

    return redirect(url_for("trips.view_trip", trip_id=trip_id))


@bp.route("/<int:trip_id>/withdraw", methods=["POST"])
@login_required
def withdraw_from_trip(trip_id):
    """Withdraw from trip announcement"""
    trip = Trip.query.get_or_404(trip_id)

    try:
        success = trip.remove_participant(current_user)
        if success:
            db.session.commit()
            flash("Uspešno ste se odjavili z izleta.", "info")
        else:
            flash("Niste prijavljeni na ta izlet.", "error")

    except Exception:
        db.session.rollback()
        flash("Napaka pri odjavi z izleta. Poskusite znova.", "error")

    return redirect(url_for("trips.view_trip", trip_id=trip_id))


@bp.route("/<int:trip_id>/comment", methods=["POST"])
@login_required
def add_comment(trip_id):
    """Add comment to trip announcement"""
    trip = Trip.query.get_or_404(trip_id)
    form = TripCommentForm()

    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            comment_type=CommentType.TRIP,
            trip_id=trip_id,
            author_id=current_user.id,
        )

        try:
            db.session.add(comment)
            db.session.commit()
            flash("Komentar je bil uspešno dodan!", "success")

        except Exception:
            db.session.rollback()
            flash("Napaka pri dodajanju komentarja. Poskusite znova.", "error")
    else:
        flash("Napaka pri dodajanju komentarja. Preverite vnešene podatke.", "error")

    return redirect(url_for("trips.view_trip", trip_id=trip_id))


@bp.route("/dashboard")
@login_required
def dashboard():
    """User's personal trip dashboard"""
    if current_user.role in [UserRole.TRIP_LEADER, UserRole.ADMIN]:
        # Trip leaders see their led trips
        led_trips = Trip.get_trips_by_leader(current_user.id)

        # Get participation in other trips
        my_participations = TripParticipant.get_user_trips(current_user.id)

        return render_template(
            "trips/leader_dashboard.html", led_trips=led_trips, my_participations=my_participations
        )
    else:
        # Regular members see their trip participations
        my_participations = TripParticipant.get_user_trips(current_user.id)

        return render_template("trips/member_dashboard.html", my_participations=my_participations)


@bp.route("/calendar")
def calendar():
    """Calendar view of trip announcements"""
    return render_template("trips/calendar.html")


@bp.route("/calendar/events")
def calendar_events():
    """JSON endpoint for FullCalendar events"""
    # Get date range from query parameters
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    # Parse dates - handle timezone format properly
    def parse_calendar_date(date_str):
        if not date_str:
            return None

        # Remove timezone information (Z or +XX:XX or -XX:XX)
        import re

        # Handle URL decoding where + becomes space
        date_str = date_str.replace(" ", "+")
        # Pattern to match timezone offset at the end
        date_str = re.sub(r"[+-]\d{2}:\d{2}$|Z$", "", date_str)

        return datetime.fromisoformat(date_str)

    start_date = parse_calendar_date(start_str)
    end_date = parse_calendar_date(end_str)

    # Build query for trips in date range
    query = Trip.query.filter(Trip.status == TripStatus.ANNOUNCED)

    if start_date:
        query = query.filter(Trip.trip_date >= start_date.date())
    if end_date:
        query = query.filter(Trip.trip_date <= end_date.date())

    trips = query.order_by(Trip.trip_date.asc()).all()

    # Convert trips to FullCalendar events format
    events = []
    for trip in trips:
        events.append(
            {
                "id": trip.id,
                "title": trip.title,
                "start": trip.trip_date.isoformat(),
                "url": url_for("trips.view_trip", trip_id=trip.id),
                "className": f"difficulty-{trip.difficulty.value}",
                "extendedProps": {
                    "destination": trip.destination,
                    "difficulty": trip.difficulty.value,
                    "difficultyLabel": trip.difficulty.slovenian_name,
                    "participantCount": len(trip.participants),
                    "maxParticipants": trip.max_participants,
                    "leader": trip.leader.name if trip.leader else "Neznano",
                },
            }
        )

    return jsonify(events)
