from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from models.user import User, UserRole, db

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Prosim vnesite email in geslo.', 'error')
            return render_template('auth/login.html')
        
        user = User.get_by_email(email)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.update_last_login()
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            
            return redirect(next_page)
        else:
            flash('Napačen email ali geslo.', 'error')
    
    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Basic validation
        if not all([email, name, password, password_confirm]):
            flash('Vsa polja so obvezna.', 'error')
            return render_template('auth/register.html')
        
        if password != password_confirm:
            flash('Gesli se ne ujemata.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Geslo mora imeti vsaj 6 znakov.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.get_by_email(email):
            flash('Uporabnik s tem email naslovom že obstaja.', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User.create_user(email=email, name=name, password=password)
        if user:
            db.session.add(user)
            db.session.commit()
            
            flash('Registracija uspešna! Čakate na odobritev administratorja.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Napaka pri registraciji. Poskusite znova.', 'error')
    
    return render_template('auth/register.html')


@bp.route('/logout')
def logout():
    """User logout"""
    logout_user()
    flash('Uspešno ste se odjavili.', 'info')
    return redirect(url_for('main.index'))