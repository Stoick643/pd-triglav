from flask import Blueprint, render_template, current_app, request, flash, redirect, url_for
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