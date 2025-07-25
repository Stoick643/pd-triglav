"""Test configuration and fixtures for pytest"""

import pytest
import tempfile
import os
from app import create_app
from models.user import db
from config import TestingConfig
from models.user import User, UserRole


@pytest.fixture
def app():
    """Create application for testing"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Update config to use temporary database
    TestingConfig.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        
        # Cleanup
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth(client):
    """Authentication helper"""
    class AuthActions:
        def __init__(self, client):
            self._client = client
        
        def login(self, email='test@example.com', password='testpass'):
            return self._client.post('/auth/login', data={
                'email': email,
                'password': password
            })
        
        def logout(self):
            return self._client.get('/auth/logout')
        
        def register(self, email='test@example.com', name='Test User', 
                    password='testpass', password_confirm='testpass'):
            return self._client.post('/auth/register', data={
                'email': email,
                'name': name,
                'password': password,
                'password_confirm': password_confirm
            })
    
    return AuthActions(client)


@pytest.fixture
def test_users(app):
    """Create test users in database"""
    def _get_users():
        """Function to get fresh user instances from database"""
        return {
            'admin': User.query.filter_by(email='admin@test.com').first(),
            'member': User.query.filter_by(email='member@test.com').first(),
            'trip_leader': User.query.filter_by(email='leader@test.com').first(),
            'pending': User.query.filter_by(email='pending@test.com').first()
        }
    
    with app.app_context():
        # Check if users already exist
        if User.query.filter_by(email='admin@test.com').first():
            return _get_users()
        
        # Admin user
        admin = User.create_user(
            email='admin@test.com',
            name='Admin User',
            password='adminpass',
            role=UserRole.ADMIN
        )
        admin.approve(UserRole.ADMIN)
        db.session.add(admin)
        
        # Regular member
        member = User.create_user(
            email='member@test.com',
            name='Member User',
            password='memberpass',
            role=UserRole.MEMBER
        )
        member.approve()
        db.session.add(member)
        
        # Trip leader
        trip_leader = User.create_user(
            email='leader@test.com',
            name='Leader User',
            password='leaderpass',
            role=UserRole.TRIP_LEADER
        )
        trip_leader.approve(UserRole.TRIP_LEADER)
        db.session.add(trip_leader)
        
        # Pending user
        pending = User.create_user(
            email='pending@test.com',
            name='Pending User',
            password='pendingpass'
        )
        db.session.add(pending)
        
        db.session.commit()
        
        return _get_users()