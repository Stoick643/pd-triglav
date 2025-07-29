from flask import Blueprint, render_template, current_app, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Home page with role-based content"""
    todays_event = None
    recent_events = []
    daily_news = []
    
    # Get today's historical event (temporarily for everyone)
    if True:  # Temporarily show to everyone
        try:
            from models.content import HistoricalEvent
            todays_event = HistoricalEvent.get_todays_event()
            
            # If no event exists, try to generate one
            if not todays_event:
                from utils.content_generation import generate_todays_historical_event
                todays_event = generate_todays_historical_event()
            
            # Get recent historical events (last 7, excluding today's)
            from utils.llm_service import format_date_standard
            from datetime import datetime
            today_date = format_date_standard(datetime.now())
            
            recent_events = HistoricalEvent.query.filter(
                HistoricalEvent.date != today_date
            ).order_by(
                HistoricalEvent.date.desc()
            ).limit(7).all()
                
        except Exception as e:
            current_app.logger.error(f"Failed to get historical events: {e}")
            # Continue without historical events
    
    # Get daily climbing news (from cache or API fallback)
    try:
        from utils.daily_news import get_daily_mountaineering_news_for_homepage
        daily_news = get_daily_mountaineering_news_for_homepage()
        if not daily_news:
            current_app.logger.info("No cached news found, this is normal on first run")
    except Exception as e:
        current_app.logger.error(f"Failed to get daily news: {e}")
        daily_news = []
    
    return render_template('index.html', todays_event=todays_event, recent_events=recent_events, daily_news=daily_news)


@bp.route('/history/event/<int:event_id>')
def historical_event_detail(event_id):
    """Display full details of a historical event"""
    try:
        from models.content import HistoricalEvent
        event = HistoricalEvent.query.get_or_404(event_id)
        return render_template('history/event_detail.html', event=event)
    except Exception as e:
        current_app.logger.error(f"Error loading historical event {event_id}: {e}")
        flash('Dogodek ni bil najden.', 'error')
        return redirect(url_for('main.index'))


@bp.route('/about')
def about():
    """About page with club information"""
    return render_template('about.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """Member dashboard - requires authentication"""
    if current_user.is_pending():
        return render_template('pending_approval.html')
    
    return render_template('dashboard.html')


@bp.route('/admin')
@login_required
def admin():
    """Admin dashboard - requires admin role"""
    if not current_user.is_admin():
        return render_template('errors/403.html'), 403
    
    from models.user import User
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
    
    return render_template('admin/dashboard.html', 
                         pending_users=pending_users,
                         approval_forms=approval_forms,
                         rejection_forms=rejection_forms)


@bp.route('/admin/approve-user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    """Approve pending user - admin only"""
    if not current_user.is_admin():
        flash('Dostop zavrnjen.', 'error')
        return redirect(url_for('main.index'))
    
    from models.user import db, User, UserRole
    from forms.admin_forms import UserApprovalForm
    
    form = UserApprovalForm()
    
    current_app.logger.warn(f"Approval form submitted for user {user_id}")
    current_app.logger.warn(f"Form data: {dict(request.form)}")
    current_app.logger.warn(f"Form validation result: {form.validate_on_submit()}")
    current_app.logger.warn(f"Form errors: {form.errors}")
    
    if not form.validate_on_submit():
        flash('Neveljaven zahtevek za odobritev.', 'error')
        current_app.logger.error(f"Form validation failed: {form.errors}")
        return redirect(url_for('main.admin'))
    
    user = User.query.get_or_404(user_id)
    
    if user.role != UserRole.PENDING:
        flash('Uporabnik ni na čakanju za odobritev.', 'warning')
        return redirect(url_for('main.admin'))
    
    try:
        user.role = UserRole.MEMBER
        user.is_approved = True
        db.session.commit()
        flash(f'Uporabnik {user.name} je bil uspešno odobren kot član.', 'success')
        current_app.logger.info(f"Admin {current_user.email} approved user {user.email}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to approve user {user.email}: {e}")
        flash(f'Napaka pri odobritvi uporabnika: {str(e)}', 'error')
    
    return redirect(url_for('main.admin'))


@bp.route('/admin/reject-user/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    """Reject pending user - admin only"""
    if not current_user.is_admin():
        flash('Dostop zavrnjen.', 'error')
        return redirect(url_for('main.index'))
    
    from models.user import db, User, UserRole
    from forms.admin_forms import UserRejectionForm
    
    form = UserRejectionForm()
    
    current_app.logger.info(f"Rejection form submitted for user {user_id}")
    current_app.logger.info(f"Form data: {dict(request.form)}")
    current_app.logger.info(f"Form validation result: {form.validate_on_submit()}")
    current_app.logger.info(f"Form errors: {form.errors}")
    
    if not form.validate_on_submit():
        flash('Neveljaven zahtevek za zavrnitev.', 'error')
        current_app.logger.error(f"Form validation failed: {form.errors}")
        return redirect(url_for('main.admin'))
    
    user = User.query.get_or_404(user_id)
    
    if user.role != UserRole.PENDING:
        flash('Uporabnik ni na čakanju za odobritev.', 'warning')
        return redirect(url_for('main.admin'))
    
    try:
        user_name = user.name
        user_email = user.email
        db.session.delete(user)
        db.session.commit()
        flash(f'Uporabnik {user_name} je bil zavrnjen in odstranjen.', 'info')
        current_app.logger.info(f"Admin {current_user.email} rejected and deleted user {user_email}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to reject user {user.email}: {e}")
        flash(f'Napaka pri zavrnitvi uporabnika: {str(e)}', 'error')
    
    return redirect(url_for('main.admin'))


@bp.route('/admin/regenerate-today-event', methods=['POST'])
@login_required
def regenerate_today_event():
    """Regenerate today's historical event - admin only"""
    if not current_user.is_admin():
        return jsonify({'error': 'Dostop zavrnjen. Potrebne so administratorske pravice.'}), 403
    
    try:
        from models.content import HistoricalEvent
        from utils.content_generation import HistoricalEventService
        from utils.llm_service import format_date_standard
        from datetime import datetime
        
        # Get today's date
        today = format_date_standard(datetime.now())
        
        # Find existing event for today
        existing_event = HistoricalEvent.get_event_for_date(today)
        
        if existing_event:
            # Regenerate existing event
            service = HistoricalEventService()
            updated_event = service.regenerate_event(existing_event.id)
            
            current_app.logger.info(f"Admin {current_user.email} regenerated event: {updated_event.title}")
            
            return jsonify({
                'success': True,
                'message': 'Dogodek je bil uspešno regeneriran.',
                'event': {
                    'id': updated_event.id,
                    'title': updated_event.title,
                    'description': updated_event.description,
                    'location': updated_event.location,
                    'people': updated_event.people_list,
                    'url': updated_event.url,
                    'url_secondary': updated_event.url_secondary,
                    'category': updated_event.category.value,
                    'full_date_string': updated_event.full_date_string,
                    'is_generated': updated_event.is_generated
                }
            })
        else:
            # Generate new event for today
            service = HistoricalEventService()
            new_event = service.generate_daily_event()
            
            current_app.logger.info(f"Admin {current_user.email} generated new event: {new_event.title}")
            
            return jsonify({
                'success': True,
                'message': 'Nov dogodek je bil uspešno ustvarjen.',
                'event': {
                    'id': new_event.id,
                    'title': new_event.title,
                    'description': new_event.description,
                    'location': new_event.location,
                    'people': new_event.people_list,
                    'url': new_event.url,
                    'url_secondary': new_event.url_secondary,
                    'category': new_event.category.value,
                    'full_date_string': new_event.full_date_string,
                    'is_generated': new_event.is_generated
                }
            })
            
    except Exception as e:
        current_app.logger.error(f"Error regenerating historical event: {e}")
        return jsonify({
            'success': False,
            'error': 'Napaka pri regeneraciji dogodka. Poskusite ponovno.'
        }), 500


@bp.route('/api/history/recent')
def get_recent_historical_events():
    """Get recent historical events for archive display"""
    try:
        from models.content import HistoricalEvent
        
        # Get pagination parameters
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 7, type=int)
        
        # Ensure reasonable limits
        limit = min(limit, 20)  # Max 20 events per request
        
        # Get recent events (excluding today's event to avoid duplication)
        from utils.llm_service import format_date_standard
        from datetime import datetime
        today = format_date_standard(datetime.now())
        
        events = HistoricalEvent.query.filter(
            HistoricalEvent.date != today
        ).order_by(
            HistoricalEvent.created_at.desc(),
            HistoricalEvent.year.desc()
        ).offset(offset).limit(limit).all()
        
        # Convert to JSON format
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'date': event.date,
                'year': event.year,
                'title': event.title,
                'description': event.description[:200] + '...' if len(event.description) > 200 else event.description,
                'location': event.location,
                'people': event.people_list[:3] if event.people_list else [],  # First 3 people
                'category': event.category.value,
                'full_date_string': event.full_date_string,
                'is_featured': event.is_featured
            })
        
        # Check if there are more events
        total_events = HistoricalEvent.query.filter(HistoricalEvent.date != today).count()
        has_more = (offset + limit) < total_events
        
        return jsonify({
            'success': True,
            'events': events_data,
            'has_more': has_more,
            'total': total_events,
            'loaded': offset + len(events_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching recent historical events: {e}")
        return jsonify({
            'success': False,
            'error': 'Napaka pri nalaganju zgodovinskih dogodkov.'
        }), 500


@bp.route('/api/historical-events')
def api_historical_events():
    """API endpoint for historical events by date"""
    try:
        from models.content import HistoricalEvent
        from datetime import datetime
        
        # Get date parameter (format: DD-MM or YYYY-MM-DD)
        date_param = request.args.get('date')
        limit = request.args.get('limit', 10, type=int)
        
        # Ensure reasonable limits
        limit = min(limit, 100)  # Max 100 events per request
        
        if not date_param:
            # If no date provided, use today's date
            from utils.llm_service import format_date_standard
            date_param = format_date_standard(datetime.now())
        
        # Parse date parameter
        if len(date_param) == 5 and '-' in date_param:
            # Format: DD-MM
            day, month = date_param.split('-')
            search_date = f"{day} {['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][int(month)-1]}"
        else:
            # Use as-is for other formats
            search_date = date_param
        
        # Query events for the specific date
        events = HistoricalEvent.query.filter(
            HistoricalEvent.date.ilike(f"%{search_date}%")
        ).order_by(
            HistoricalEvent.year.desc(),
            HistoricalEvent.created_at.desc()
        ).limit(limit).all()
        
        # Convert to JSON format
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'date': event.date,
                'year': event.year,
                'title': event.title,
                'description': event.description,
                'location': event.location,
                'people': event.people_list if event.people_list else [],
                'category': event.category.value,
                'full_date_string': event.full_date_string,
                'is_featured': event.is_featured,
                'url': event.url,
                'url_secondary': event.url_secondary
            })
        
        return jsonify(events_data)
        
    except ValueError as e:
        # Invalid date format
        return jsonify({
            'error': 'Invalid date format. Use DD-MM or YYYY-MM-DD.'
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Error fetching historical events: {e}")
        return jsonify({
            'error': 'Server error while fetching events.'
        }), 500