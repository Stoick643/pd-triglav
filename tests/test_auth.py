"""Test authentication functionality"""

import pytest
from flask import url_for
from models.user import User, UserRole
from models.user import db

# Mark auth tests as fast (they use mocked forms now)
pytestmark = [pytest.mark.fast, pytest.mark.auth]


def test_register_new_user(client, app):
    """Test user registration"""
    # Test GET request
    response = client.get('/auth/register')
    assert response.status_code == 200
    
    # Test successful registration
    response = client.post('/auth/register', data={
        'name': 'New User',
        'email': 'newuser@test.com',
        'password': 'password123',
        'password_confirm': 'password123'
    })
    
    assert response.status_code == 302  # Redirect after success
    
    # Check user was created in database
    with app.app_context():
        user = User.get_by_email('newuser@test.com')
        assert user is not None
        assert user.name == 'New User'
        assert user.is_pending() is True


def test_register_validation_errors(client):
    """Test registration form validation"""
    # Missing fields
    response = client.post('/auth/register', data={
        'name': '',
        'email': 'test@test.com',
        'password': 'pass',
        'password_confirm': 'pass'
    })
    assert 'Vsa polja so obvezna'.encode('utf-8') in response.data
    
    # Password mismatch
    response = client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@test.com',
        'password': 'password1',
        'password_confirm': 'password2'
    })
    assert 'Gesli se ne ujemata'.encode('utf-8') in response.data
    
    # Short password
    response = client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@test.com',
        'password': '123',
        'password_confirm': '123'
    })
    assert b'vsaj 6 znakov' in response.data


def test_login_logout(client, app, test_users):
    """Test user login and logout"""
    # Test login with valid credentials
    response = client.post('/auth/login', data={
        'email': 'member@test.com',
        'password': 'memberpass'
    })
    assert response.status_code == 302  # Redirect after login
    
    # Test that we can access dashboard after login
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert 'Dobrodošli'.encode('utf-8') in response.data
    
    # Test logout
    response = client.get('/auth/logout')
    assert response.status_code == 302  # Redirect after logout
    
    # Test that dashboard requires login again
    response = client.get('/dashboard')
    assert response.status_code == 302  # Redirect to login


def test_login_invalid_credentials(client, test_users):
    """Test login with invalid credentials"""
    # Wrong password
    response = client.post('/auth/login', data={
        'email': 'member@test.com',
        'password': 'wrongpassword'
    })
    assert 'Napačen email ali geslo'.encode('utf-8') in response.data
    
    # Non-existent user
    response = client.post('/auth/login', data={
        'email': 'nonexistent@test.com',
        'password': 'password'
    })
    assert 'Napačen email ali geslo'.encode('utf-8') in response.data


def test_pending_user_dashboard(client, app, test_users):
    """Test that pending users see pending approval page"""
    # Login as pending user
    response = client.post('/auth/login', data={
        'email': 'pending@test.com',
        'password': 'pendingpass'
    })
    assert response.status_code == 302
    
    # Access dashboard should show pending approval
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert 'Čaka na odobritev'.encode('utf-8') in response.data


def test_admin_access(client, test_users):
    """Test admin access control"""
    # Login as regular member
    client.post('/auth/login', data={
        'email': 'member@test.com',
        'password': 'memberpass'
    })
    
    # Try to access admin page
    response = client.get('/admin')
    assert response.status_code == 403  # Forbidden
    
    # Logout and login as admin
    client.get('/auth/logout')
    client.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'adminpass'
    })
    
    # Admin should be able to access admin page
    response = client.get('/admin')
    assert response.status_code == 200
    assert 'Administratorska plošča'.encode('utf-8') in response.data