"""Test OAuth integration functionality"""

from unittest.mock import patch
from models.user import User, UserRole, db


def test_google_login_redirect(app, client):
    """Test that Google login initiates OAuth flow"""
    with app.app_context():
        with patch("routes.auth.oauth.google") as mock_google:
            mock_google.authorize_redirect.return_value = "redirect_response"

            client.get("/auth/google/login")

            # Should call authorize_redirect with correct URI
            mock_google.authorize_redirect.assert_called_once()
            args = mock_google.authorize_redirect.call_args[0]
            assert "/auth/google/callback" in args[0]


def test_google_login_stores_next_url(app, client):
    """Test that next URL is stored in session during OAuth"""
    with app.app_context():
        with patch("routes.auth.oauth.google") as mock_google:
            mock_google.authorize_redirect.return_value = "redirect"

            with client.session_transaction() as sess:
                # Should be empty initially
                assert "next_url" not in sess

            # Login with next parameter
            client.get("/auth/google/login?next=/some/protected/page")

            with client.session_transaction() as sess:
                assert sess.get("next_url") == "/some/protected/page"


@patch("routes.auth.oauth.google")
def test_google_callback_new_user_creation(mock_google, app, client):
    """Test creating new user from Google OAuth callback"""
    with app.app_context():
        # Mock Google response
        mock_token = {
            "userinfo": {"sub": "google123456", "email": "new.user@gmail.com", "name": "New User"}
        }
        mock_google.authorize_access_token.return_value = mock_token

        # Ensure user doesn't exist
        assert User.get_by_google_id("google123456") is None
        assert User.get_by_email("new.user@gmail.com") is None

        # Call OAuth callback
        response = client.get("/auth/google/callback")

        # Should redirect to dashboard
        assert response.status_code == 302
        assert "/dashboard" in response.location or response.location.endswith("/")

        # User should be created
        user = User.get_by_google_id("google123456")
        assert user is not None
        assert user.email == "new.user@gmail.com"
        assert user.name == "New User"
        assert user.role == UserRole.PENDING
        assert not user.is_approved


@patch("routes.auth.oauth.google")
def test_google_callback_existing_user_by_google_id(mock_google, app, client, test_users):
    """Test login with existing Google ID"""
    with app.app_context():
        # Setup existing user with Google ID
        existing_user = test_users["member"]
        existing_user.google_id = "existing_google_id"
        db.session.commit()

        # Mock Google response
        mock_token = {
            "userinfo": {
                "sub": "existing_google_id",
                "email": existing_user.email,
                "name": existing_user.name,
            }
        }
        mock_google.authorize_access_token.return_value = mock_token

        # Call OAuth callback
        response = client.get("/auth/google/callback")

        # Should login successfully
        assert response.status_code == 302

        # User should be the existing one
        user = User.get_by_google_id("existing_google_id")
        assert user.id == existing_user.id


@patch("routes.auth.oauth.google")
def test_google_callback_link_existing_email_account(mock_google, app, client, test_users):
    """Test linking Google account to existing email-based account"""
    with app.app_context():
        existing_user = test_users["member"]
        original_google_id = existing_user.google_id

        # Mock Google response with same email but new Google ID
        mock_token = {
            "userinfo": {
                "sub": "new_google_id_12345",
                "email": existing_user.email,  # Same email as existing user
                "name": existing_user.name,
            }
        }
        mock_google.authorize_access_token.return_value = mock_token

        # Call OAuth callback
        response = client.get("/auth/google/callback")

        # Should link account successfully
        assert response.status_code == 302

        # Get fresh user from database
        updated_user = User.get_by_email(existing_user.email)

        # Google ID should be updated
        assert updated_user.google_id == "new_google_id_12345"
        assert updated_user.google_id != original_google_id


@patch("routes.auth.oauth.google")
def test_google_callback_missing_required_fields(mock_google, app, client):
    """Test OAuth callback with missing required user info"""
    with app.app_context():
        # Mock incomplete Google response
        mock_token = {
            "userinfo": {
                "sub": "google123",
                "email": "test@gmail.com",
                # Missing 'name' field
            }
        }
        mock_google.authorize_access_token.return_value = mock_token

        # Call OAuth callback
        response = client.get("/auth/google/callback")

        # Should redirect to login with error
        assert response.status_code == 302
        assert "/auth/login" in response.location


@patch("routes.auth.oauth.google")
def test_google_callback_token_error(mock_google, app, client):
    """Test OAuth callback with token authorization error"""
    with app.app_context():
        # Mock token error
        mock_google.authorize_access_token.side_effect = Exception("OAuth token error")

        # Call OAuth callback
        response = client.get("/auth/google/callback")

        # Should redirect to login with error
        assert response.status_code == 302
        assert "/auth/login" in response.location


@patch("routes.auth.oauth.google")
def test_google_callback_userinfo_from_id_token(mock_google, app, client):
    """Test OAuth callback when userinfo comes from ID token"""
    with app.app_context():
        # Mock token without userinfo but with id_token
        mock_token = {}
        mock_google.authorize_access_token.return_value = mock_token
        mock_google.parse_id_token.return_value = {
            "sub": "id_token_google_id",
            "email": "idtoken.user@gmail.com",
            "name": "ID Token User",
        }

        # Call OAuth callback
        response = client.get("/auth/google/callback")

        # Should create user successfully
        assert response.status_code == 302

        # User should be created from ID token
        user = User.get_by_google_id("id_token_google_id")
        assert user is not None
        assert user.email == "idtoken.user@gmail.com"
        assert user.name == "ID Token User"


def test_google_login_authenticated_user_redirect(app, client, test_users):
    """Test that authenticated users are redirected from Google login"""
    with app.app_context():
        user = test_users["member"]

        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        response = client.get("/auth/google/login")

        # Should redirect to dashboard without starting OAuth
        assert response.status_code == 302


@patch("routes.auth.oauth.google")
def test_google_callback_next_url_redirect(mock_google, app, client):
    """Test that OAuth callback redirects to stored next URL"""
    with app.app_context():
        # Mock successful Google response
        mock_token = {
            "userinfo": {
                "sub": "callback_test_id",
                "email": "callback@gmail.com",
                "name": "Callback Test",
            }
        }
        mock_google.authorize_access_token.return_value = mock_token

        # Set next URL in session
        with client.session_transaction() as sess:
            sess["next_url"] = "/trips/create"

        # Call OAuth callback
        response = client.get("/auth/google/callback")

        # Should redirect to the stored next URL
        assert response.status_code == 302
        assert "/trips/create" in response.location

        # Session should be cleaned up
        with client.session_transaction() as sess:
            assert "next_url" not in sess


@patch("routes.auth.oauth.google")
def test_google_callback_user_role_assignment(mock_google, app, client):
    """Test that new OAuth users get correct role assignment"""
    with app.app_context():
        # Mock Google response for new user
        mock_token = {
            "userinfo": {
                "sub": "role_test_google_id",
                "email": "role.test@gmail.com",
                "name": "Role Test User",
            }
        }
        mock_google.authorize_access_token.return_value = mock_token

        # Call OAuth callback
        client.get("/auth/google/callback")

        # Check user role
        user = User.get_by_google_id("role_test_google_id")
        assert user.role == UserRole.PENDING
        assert not user.is_approved

        # User should not be able to access protected features until approved
        assert user.role == UserRole.PENDING
        assert not user.is_approved


def test_oauth_integration_with_existing_login_flow(app, client, test_users):
    """Test that OAuth and regular login can coexist"""
    with app.app_context():
        user = test_users["member"]

        # User should be able to login with regular credentials
        response = client.post(
            "/auth/login",
            data={
                "email": user.email,
                "password": "memberpass",  # Use correct password from conftest
            },
        )
        assert response.status_code == 302

        # Logout
        client.get("/auth/logout")

        # If user had Google ID, they could also login via OAuth
        user.google_id = "oauth_integration_test"
        db.session.commit()

        with patch("routes.auth.oauth.google") as mock_google:
            mock_token = {
                "userinfo": {
                    "sub": "oauth_integration_test",
                    "email": user.email,
                    "name": user.name,
                }
            }
            mock_google.authorize_access_token.return_value = mock_token

            response = client.get("/auth/google/callback")
            assert response.status_code == 302
