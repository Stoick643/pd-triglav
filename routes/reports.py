"""Trip reports routes for sharing experiences"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_, desc
from sqlalchemy.orm import joinedload

from models.user import db, User, UserRole
from models.trip import Trip
from models.content import TripReport, Comment, CommentType
from forms.trip_forms import TripReportForm, TripReportFilterForm, TripCommentForm

bp = Blueprint('reports', __name__)


@bp.route('/')
def list_reports():
    """Display list of trip reports with filtering"""
    form = TripReportFilterForm()
    
    # Populate trip choices for filter
    completed_trips = Trip.query.filter(Trip.status.in_(['completed', 'announced'])).order_by(Trip.trip_date.desc()).all()
    form.trip_id.choices = [('', 'Vsi izleti')] + [(trip.id, f"{trip.title} ({trip.trip_date.strftime('%d.%m.%Y')})") for trip in completed_trips]
    
    # Base query for published reports with eager loading of trip relationship
    query = TripReport.query.options(joinedload(TripReport.trip)).filter_by(is_published=True)
    
    # Apply filters if form is submitted
    if form.validate_on_submit():
        if form.search.data:
            search_term = f"%{form.search.data}%"
            query = query.join(User).filter(or_(
                TripReport.title.ilike(search_term),
                TripReport.summary.ilike(search_term),
                User.name.ilike(search_term)
            ))
        
        if form.trip_id.data:
            query = query.filter(TripReport.trip_id == form.trip_id.data)
        
        if form.author.data:
            query = query.join(User).filter(User.name.ilike(f"%{form.author.data}%"))
        
        if form.featured_only.data == 'featured':
            query = query.filter(TripReport.featured == True)
        elif form.featured_only.data == 'recent':
            # Show only reports from last 30 days
            from datetime import date, timedelta
            recent_date = date.today() - timedelta(days=30)
            query = query.filter(TripReport.created_at >= recent_date)
    
    # Order by creation date, featured first
    reports = query.order_by(desc(TripReport.featured), desc(TripReport.created_at)).all()
    
    return render_template('reports/list.html', reports=reports, form=form)


@bp.route('/<int:report_id>')
def view_report(report_id):
    """Display individual trip report with comments"""
    report = TripReport.query.options(joinedload(TripReport.trip)).filter_by(id=report_id).first_or_404()
    
    # Check if report is published or user is author/admin
    if not report.is_published:
        if not current_user.is_authenticated or (current_user.id != report.author_id and not current_user.is_admin()):
            abort(404)
    
    # Get comments for this report
    comments = Comment.get_comments_for_report(report_id)
    
    # Comment form for logged-in users
    comment_form = TripCommentForm() if current_user.is_authenticated else None
    
    return render_template('reports/detail.html', 
                         report=report, 
                         comments=comments,
                         comment_form=comment_form)


@bp.route('/create', methods=['GET', 'POST'])
@bp.route('/create/<int:trip_id>', methods=['GET', 'POST'])
@login_required
def create_report(trip_id=None):
    """Create new trip report, optionally for specific trip"""
    # If trip_id provided, check if user participated in that trip
    trip = None
    if trip_id:
        trip = Trip.query.get_or_404(trip_id)
        
        # Check if user participated in this trip
        from models.trip import TripParticipant, ParticipantStatus
        participation = TripParticipant.query.filter_by(
            trip_id=trip_id, 
            user_id=current_user.id,
            status=ParticipantStatus.CONFIRMED
        ).first()
        
        if not participation and not current_user.is_admin():
            flash('Poročilo lahko napišete samo za izlete, na katerih ste sodelovali.', 'error')
            return redirect(url_for('reports.list_reports'))
        
        # Check if user already wrote a report for this trip
        existing_report = TripReport.query.filter_by(
            trip_id=trip_id,
            author_id=current_user.id
        ).first()
        
        if existing_report:
            flash('Za ta izlet ste že napisali poročilo.', 'warning')
            return redirect(url_for('reports.view_report', report_id=existing_report.id))
    
    form = TripReportForm()
    
    # Get list of trips user participated in for dropdown
    # TEMPORARY: Allow reports for any trip status for testing purposes
    if current_user.is_admin():
        # Admins can write reports for any trip (TESTING MODE)
        available_trips = Trip.query.order_by(Trip.trip_date.desc()).all()
    else:
        # Regular users can write reports for trips they participated in (TESTING MODE - allow any status)
        from models.trip import TripParticipant, ParticipantStatus
        participations = TripParticipant.query.filter_by(
            user_id=current_user.id,
            status=ParticipantStatus.CONFIRMED
        ).all()
        available_trips = [p.trip for p in participations]  # Remove status filter for testing
    
    # Remove trips that already have reports from this user
    existing_reports = TripReport.query.filter_by(author_id=current_user.id).all()
    existing_trip_ids = {r.trip_id for r in existing_reports}
    available_trips = [t for t in available_trips if t.id not in existing_trip_ids]
    
    if form.validate_on_submit():
        # Determine if report should be published
        is_published = form.is_published.data == 'true'
        
        # Get trip_id properly from form or URL parameter
        selected_trip_id = trip_id
        if not selected_trip_id:
            selected_trip_id = request.form.get('trip_id')
            if selected_trip_id:
                selected_trip_id = int(selected_trip_id)
        
        if not selected_trip_id:
            flash('Morate izbrati izlet za poročilo.', 'error')
            return redirect(url_for('reports.create_report'))
        
        # Verify the trip exists
        from models.trip import Trip
        selected_trip = Trip.query.get(selected_trip_id)
        if not selected_trip:
            flash('Izbrani izlet ne obstaja.', 'error')
            return redirect(url_for('reports.create_report'))
        
        report = TripReport(
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            weather_conditions=form.weather_conditions.data,
            trail_conditions=form.trail_conditions.data,
            is_published=is_published,
            trip_id=selected_trip_id,
            author_id=current_user.id
        )
        
        try:
            db.session.add(report)
            db.session.commit()
            
            if is_published:
                flash(f'Poročilo "{report.title}" je bilo uspešno objavljeno!', 'success')
            else:
                flash(f'Poročilo "{report.title}" je bilo shranjeno kot osnutek.', 'info')
            
            return redirect(url_for('reports.view_report', report_id=report.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Napaka pri shranjevanju poročila. Poskusite znova.', 'error')
    
    return render_template('reports/create.html', 
                         form=form, 
                         trip=trip, 
                         available_trips=available_trips)


@bp.route('/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_report(report_id):
    """Edit existing trip report"""
    report = TripReport.query.options(joinedload(TripReport.trip)).filter_by(id=report_id).first_or_404()
    
    # Only author or admin can edit
    if not (current_user.id == report.author_id or current_user.is_admin()):
        flash('Lahko urejate le svoja poročila.', 'error')
        return abort(403)
    
    form = TripReportForm(obj=report)
    
    # Set initial form values
    form.is_published.data = 'true' if report.is_published else 'false'
    
    if form.validate_on_submit():
        # Update report with form data
        report.title = form.title.data
        report.summary = form.summary.data
        report.content = form.content.data
        report.weather_conditions = form.weather_conditions.data
        report.trail_conditions = form.trail_conditions.data
        report.is_published = form.is_published.data == 'true'
        report.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash(f'Poročilo "{report.title}" je bilo uspešno posodobljeno!', 'success')
            return redirect(url_for('reports.view_report', report_id=report.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Napaka pri posodabljanju poročila. Poskusite znova.', 'error')
    
    return render_template('reports/edit.html', form=form, report=report)


@bp.route('/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    """Delete trip report"""
    report = TripReport.query.options(joinedload(TripReport.trip)).filter_by(id=report_id).first_or_404()
    
    # Only author or admin can delete
    if not (current_user.id == report.author_id or current_user.is_admin()):
        flash('Lahko brišete le svoja poročila.', 'error')
        return abort(403)
    
    try:
        report_title = report.title
        db.session.delete(report)
        db.session.commit()
        
        flash(f'Poročilo "{report_title}" je bilo uspešno izbrisano.', 'success')
        return redirect(url_for('reports.list_reports'))
        
    except Exception as e:
        db.session.rollback()
        flash('Napaka pri brisanju poročila. Poskusite znova.', 'error')
        return redirect(url_for('reports.view_report', report_id=report_id))


@bp.route('/<int:report_id>/toggle-featured', methods=['POST'])
@login_required
def toggle_featured(report_id):
    """Toggle featured status of report (admin only)"""
    if not current_user.is_admin():
        flash('Samo administratorji lahko označujejo poročila.', 'error')
        return abort(403)
    
    report = TripReport.query.options(joinedload(TripReport.trip)).filter_by(id=report_id).first_or_404()
    
    try:
        report.featured = not report.featured
        db.session.commit()
        
        status = 'označeno' if report.featured else 'odznačeno'
        flash(f'Poročilo je bilo {status} kot zanimivo.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Napaka pri spreminjanju statusa poročila.', 'error')
    
    return redirect(url_for('reports.view_report', report_id=report_id))


@bp.route('/<int:report_id>/comment', methods=['POST'])
@login_required
def add_comment(report_id):
    """Add comment to trip report"""
    report = TripReport.query.options(joinedload(TripReport.trip)).filter_by(id=report_id).first_or_404()
    
    # Check if report is published
    if not report.is_published and current_user.id != report.author_id and not current_user.is_admin():
        abort(404)
    
    form = TripCommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            comment_type=CommentType.TRIP_REPORT,
            trip_report_id=report_id,
            author_id=current_user.id
        )
        
        try:
            db.session.add(comment)
            db.session.commit()
            flash('Komentar je bil uspešno dodan!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Napaka pri dodajanju komentarja. Poskusite znova.', 'error')
    else:
        flash('Napaka pri dodajanju komentarja. Preverite vnešene podatke.', 'error')
    
    return redirect(url_for('reports.view_report', report_id=report_id))


@bp.route('/my-reports')
@login_required
def my_reports():
    """User's personal trip reports dashboard"""
    # Get user's reports (published and drafts) with eager loading
    reports = TripReport.query.options(joinedload(TripReport.trip)).filter_by(author_id=current_user.id)\
        .order_by(desc(TripReport.created_at)).all()
    
    # Get trips user can write reports for
    # TEMPORARY: Allow reports for any trip status for testing purposes
    if current_user.is_admin():
        available_trips = Trip.query.order_by(Trip.trip_date.desc()).all()
    else:
        from models.trip import TripParticipant, ParticipantStatus
        participations = TripParticipant.query.filter_by(
            user_id=current_user.id,
            status=ParticipantStatus.CONFIRMED
        ).all()
        available_trips = [p.trip for p in participations]  # Remove status filter for testing
    
    # Remove trips that already have reports
    existing_trip_ids = {r.trip_id for r in reports}
    available_trips = [t for t in available_trips if t.id not in existing_trip_ids]
    
    return render_template('reports/my_reports.html', 
                         reports=reports, 
                         available_trips=available_trips)