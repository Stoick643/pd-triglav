from flask import Blueprint, render_template, current_app
from flask_login import current_user, login_required

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Home page with role-based content"""
    return render_template('index.html')


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