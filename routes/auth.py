from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, current_user
from authlib.integrations.flask_client import OAuth
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


# Initialize OAuth
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with app"""
    oauth.init_app(app)
    
    # Register Google OAuth provider
    google = oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    return google


@bp.route('/google/login')
def google_login():
    """Initiate Google OAuth login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Store the next URL in session
    session['next_url'] = request.args.get('next')
    
    # Create redirect URI
    redirect_uri = url_for('auth.google_callback', _external=True)
    
    # Get Google OAuth instance
    google = oauth.google
    return google.authorize_redirect(redirect_uri)


@bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Get Google OAuth instance
        google = oauth.google
        token = google.authorize_access_token()
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            user_info = google.parse_id_token(token)
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not all([google_id, email, name]):
            flash('Napaka pri pridobivanju podatkov iz Google računa.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user exists by Google ID
        user = User.get_by_google_id(google_id)
        
        if not user:
            # Check if user exists by email
            user = User.get_by_email(email)
            if user:
                # Link existing account with Google
                user.google_id = google_id
                db.session.commit()
                flash('Vaš račun je bil povezan z Google prijavo.', 'success')
            else:
                # Create new user account
                user = User.create_user(
                    email=email,
                    name=name,
                    google_id=google_id,
                    role=UserRole.PENDING
                )
                if user:
                    db.session.add(user)
                    db.session.commit()
                    flash('Račun ustvarjen z Google prijavo. Čakate na odobritev administratorja.', 'success')
                else:
                    flash('Napaka pri ustvarjanju računa.', 'error')
                    return redirect(url_for('auth.login'))
        
        # Log in the user
        login_user(user, remember=True)
        user.update_last_login()
        
        # Redirect to next page or dashboard
        next_page = session.pop('next_url', None)
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
        
    except Exception as e:
        current_app.logger.error(f'Google OAuth error: {str(e)}')
        flash('Napaka pri Google prijavi. Poskusite znova.', 'error')
        return redirect(url_for('auth.login'))