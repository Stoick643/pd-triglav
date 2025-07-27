from flask import Blueprint, render_template, current_app, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Home page with role-based content"""
    todays_event = None
    
    # Get today's historical event (temporarily for everyone)
    if True:  # Temporarily show to everyone
        try:
            from models.content import HistoricalEvent
            todays_event = HistoricalEvent.get_todays_event()
            
            # If no event exists, try to generate one
            if not todays_event:
                from utils.content_generation import generate_todays_historical_event
                todays_event = generate_todays_historical_event()
                
        except Exception as e:
            current_app.logger.error(f"Failed to get today's historical event: {e}")
            # Continue without historical event
    
    return render_template('index.html', todays_event=todays_event)


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
    pending_users = User.get_pending_users()
    
    return render_template('admin/dashboard.html', pending_users=pending_users)


@bp.route('/admin/approve-user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    """Approve pending user - admin only"""
    if not current_user.is_admin():
        flash('Dostop zavrnjen.', 'error')
        return redirect(url_for('main.index'))
    
    from models.user import db, User, UserRole
    user = User.query.get_or_404(user_id)
    
    if user.role != UserRole.PENDING:
        flash('Uporabnik ni na čakanju za odobritev.', 'warning')
        return redirect(url_for('main.admin'))
    
    try:
        user.role = UserRole.MEMBER
        db.session.commit()
        flash(f'Uporabnik {user.name} je bil uspešno odobren kot član.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Napaka pri odobritvi uporabnika.', 'error')
    
    return redirect(url_for('main.admin'))


@bp.route('/admin/reject-user/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    """Reject pending user - admin only"""
    if not current_user.is_admin():
        flash('Dostop zavrnjen.', 'error')
        return redirect(url_for('main.index'))
    
    from models.user import db, User, UserRole
    user = User.query.get_or_404(user_id)
    
    if user.role != UserRole.PENDING:
        flash('Uporabnik ni na čakanju za odobritev.', 'warning')
        return redirect(url_for('main.admin'))
    
    try:
        user_name = user.name
        db.session.delete(user)
        db.session.commit()
        flash(f'Uporabnik {user_name} je bil zavrnjen in odstranjen.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Napaka pri zavrnitvi uporabnika.', 'error')
    
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