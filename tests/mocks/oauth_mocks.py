"""
Mock OAuth services for testing
Provides realistic OAuth responses without making real external calls
"""

from typing import Dict


class MockOAuthProvider:
    """Mock OAuth provider (Google, GitHub, etc.)"""

    def __init__(self, provider_name: str = "google"):
        self.provider_name = provider_name
        self._tokens: dict[str, str] = {}
        self._user_profiles: dict[str, dict[str, str]] = {}
        self.call_count = 0

    def authorize(self, redirect_uri: str, **kwargs) -> str:
        """Mock OAuth authorization URL generation"""
        self.call_count += 1
        state = kwargs.get("state", f"mock-state-{self.call_count}")

        return (
            f"https://{self.provider_name}.com/oauth/authorize?"
            f"client_id=mock_client_id&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}&"
            f"scope=openid email profile"
        )

    def authorize_access_token(self, **kwargs) -> Dict:
        """Mock access token exchange"""
        self.call_count += 1

        # Simulate successful token exchange
        token_data = {
            "access_token": f"mock_access_token_{self.call_count}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": f"mock_refresh_token_{self.call_count}",
            "scope": "openid email profile",
            "id_token": f"mock_id_token_{self.call_count}",
        }

        self._tokens[token_data["access_token"]] = token_data
        return token_data

    def get_user_info(self, token: str) -> Dict:
        """Mock user info retrieval"""
        if token not in self._tokens:
            raise Exception("Invalid token")

        # Return mock user profile based on provider
        if self.provider_name == "google":
            return {
                "sub": f"mock_google_id_{self.call_count}",
                "email": "mockuser@gmail.com",
                "email_verified": True,
                "name": "Mock User",
                "given_name": "Mock",
                "family_name": "User",
                "picture": "https://mock-avatar.googleapis.com/photo.jpg",
                "locale": "sl",
            }
        else:
            return {
                "id": f"mock_{self.provider_name}_id_{self.call_count}",
                "email": f"mockuser@{self.provider_name}.com",
                "name": "Mock User",
                "avatar_url": f"https://avatars.{self.provider_name}.com/mock",
            }


class MockOAuth:
    """Mock OAuth client manager"""

    def __init__(self):
        self.providers = {}
        self._app = None

    def init_app(self, app):
        """Mock OAuth initialization with Flask app"""
        self._app = app

    def register(self, name: str, **kwargs) -> MockOAuthProvider:
        """Register a mock OAuth provider"""
        provider = MockOAuthProvider(name)
        self.providers[name] = provider
        return provider

    def create_client(self, name: str):
        """Create/get OAuth client"""
        if name not in self.providers:
            self.providers[name] = MockOAuthProvider(name)
        return self.providers[name]


class MockGoogleOAuth:
    """Specific mock for Google OAuth integration"""

    def __init__(self):
        self.provider = MockOAuthProvider("google")
        self._login_sessions = {}

    def get_google_login_url(self, next_url: str | None = None) -> str:
        """Get Google OAuth login URL"""
        state = f"mock_state_{len(self._login_sessions)}"
        if next_url:
            self._login_sessions[state] = {"next": next_url}

        return self.provider.authorize(
            redirect_uri="http://localhost:5000/auth/google/callback", state=state
        )

    def handle_google_callback(self, code: str, state: str) -> Dict:
        """Handle Google OAuth callback"""
        # Exchange code for token
        token_response = self.provider.authorize_access_token(code=code)

        # Get user info
        user_info = self.provider.get_user_info(token_response["access_token"])

        # Add session info
        session_info = self._login_sessions.get(state, {})

        return {
            "user_info": user_info,
            "token": token_response,
            "next_url": session_info.get("next"),
            "state": state,
        }

    def verify_google_token(self, token: str) -> bool:
        """Verify Google token validity"""
        return token in self.provider._tokens


def create_mock_oauth():
    """Create a mock OAuth manager"""
    return MockOAuth()


def create_mock_google_oauth():
    """Create a mock Google OAuth handler"""
    return MockGoogleOAuth()


# Patch helpers for OAuth testing
def patch_oauth_services():
    """Returns patches for OAuth service components"""
    return [
        ("authlib.integrations.flask_client.OAuth", MockOAuth),
    ]


def patch_google_oauth():
    """Returns patches specific to Google OAuth"""
    mock_oauth = MockOAuth()
    google_client = mock_oauth.register("google")

    return [
        ("routes.auth.oauth", mock_oauth),
        ("routes.auth.oauth.google", google_client),
    ]


# Mock OAuth flow scenarios
MOCK_OAUTH_SCENARIOS = {
    "google_success": {
        "authorization_url": "https://google.com/oauth/authorize?client_id=mock_client_id",
        "token_response": {
            "access_token": "mock_google_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        "user_info": {
            "sub": "mock_google_user_id",
            "email": "testuser@gmail.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
        },
    },
    "oauth_error": {"error": "access_denied", "error_description": "The user denied the request"},
    "invalid_token": {
        "error": "invalid_token",
        "error_description": "The access token provided is invalid",
    },
    "network_error": {
        "error": "network_error",
        "error_description": "Unable to connect to OAuth provider",
    },
}


# Helper functions for testing OAuth flows
def simulate_google_login_flow():
    """Simulate a complete Google login flow"""
    oauth = MockGoogleOAuth()

    # Step 1: Get authorization URL
    auth_url = oauth.get_google_login_url(next_url="/dashboard")

    # Step 2: Simulate user authorization and callback
    mock_code = "mock_authorization_code"
    mock_state = "mock_state_0"

    # Step 3: Handle callback
    result = oauth.handle_google_callback(mock_code, mock_state)

    return {
        "auth_url": auth_url,
        "callback_result": result,
        "user_email": result["user_info"]["email"],
        "user_name": result["user_info"]["name"],
    }


def simulate_oauth_error_flow():
    """Simulate OAuth error scenarios"""
    oauth = MockGoogleOAuth()

    # Simulate various error conditions
    errors = []

    try:
        # Invalid token
        oauth.provider.get_user_info("invalid_token")
    except Exception as e:
        errors.append({"type": "invalid_token", "error": str(e)})

    return {"errors": errors}
