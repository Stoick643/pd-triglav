"""Test Flask application startup and basic functionality"""

import pytest
from app import create_app
from models.user import db
from config import TestingConfig

# Mark all tests in this file as fast route tests
pytestmark = [pytest.mark.fast, pytest.mark.routes]


def test_app_creation():
    """Test that app can be created successfully"""
    app = create_app(TestingConfig)
    assert app is not None
    assert app.config["TESTING"] is True


def test_app_context(app):
    """Test app context works correctly"""
    with app.app_context():
        assert db is not None


def test_home_page(client):
    """Test home page loads correctly"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"PD Triglav" in response.data
    assert "Dobrodošli".encode("utf-8") in response.data


def test_about_page(client):
    """Test about page loads correctly"""
    response = client.get("/about")
    assert response.status_code == 200
    assert "O Planinskem društvu".encode("utf-8") in response.data


def test_login_page_get(client):
    """Test login page displays correctly"""
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Prijava" in response.data
    assert b"email" in response.data
    assert b"password" in response.data


def test_register_page_get(client):
    """Test register page displays correctly"""
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"Registracija" in response.data
    assert b"name" in response.data
    assert b"email" in response.data


def test_dashboard_requires_login(client):
    """Test dashboard redirects to login when not authenticated"""
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_admin_requires_login(client):
    """Test admin page redirects to login when not authenticated"""
    response = client.get("/admin")
    assert response.status_code == 302
    assert "/auth/login" in response.location
