"""Test User model functionality"""

import pytest
from models.user import User, UserRole
from models.user import db

# Mark all tests in this file as fast model tests
pytestmark = [pytest.mark.fast, pytest.mark.models]


def test_user_creation(app):
    """Test basic user creation"""
    with app.app_context():
        user = User.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass'
        )
        
        assert user is not None
        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.role == UserRole.PENDING
        assert user.is_approved is False


def test_password_hashing(app):
    """Test password hashing and checking"""
    with app.app_context():
        user = User.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass'
        )
        
        # Password should be hashed
        assert user.password_hash is not None
        assert user.password_hash != 'testpass'
        
        # Should be able to check password
        assert user.check_password('testpass') is True
        assert user.check_password('wrongpass') is False


def test_user_roles(app):
    """Test user role checking methods"""
    with app.app_context():
        # Pending user
        pending = User.create_user('pending@test.com', 'Pending', 'pass')
        assert pending.is_pending() is True
        assert pending.is_member() is False
        assert pending.is_trip_leader() is False
        assert pending.is_admin() is False
        
        # Member user
        member = User.create_user('member@test.com', 'Member', 'pass')
        member.approve(UserRole.MEMBER)
        assert member.is_pending() is False
        assert member.is_member() is True
        assert member.is_trip_leader() is False
        assert member.is_admin() is False
        
        # Trip leader
        leader = User.create_user('leader@test.com', 'Leader', 'pass')
        leader.approve(UserRole.TRIP_LEADER)
        assert leader.is_pending() is False
        assert leader.is_member() is True
        assert leader.is_trip_leader() is True
        assert leader.is_admin() is False
        
        # Admin user
        admin = User.create_user('admin@test.com', 'Admin', 'pass')
        admin.approve(UserRole.ADMIN)
        assert admin.is_pending() is False
        assert admin.is_member() is True
        assert admin.is_trip_leader() is True
        assert admin.is_admin() is True


def test_user_approval(app):
    """Test user approval and rejection"""
    with app.app_context():
        user = User.create_user('test@test.com', 'Test', 'pass')
        
        # Initially pending
        assert user.is_approved is False
        assert user.role == UserRole.PENDING
        
        # Approve as member
        user.approve(UserRole.MEMBER)
        assert user.is_approved is True
        assert user.role == UserRole.MEMBER
        
        # Reject
        user.reject()
        assert user.is_approved is False
        assert user.role == UserRole.PENDING


def test_duplicate_email(app):
    """Test that duplicate emails are not allowed"""
    with app.app_context():
        # Create first user
        user1 = User.create_user('test@test.com', 'User 1', 'pass')
        db.session.add(user1)
        db.session.commit()
        
        # Try to create second user with same email
        user2 = User.create_user('test@test.com', 'User 2', 'pass')
        assert user2 is None


def test_get_user_methods(app):
    """Test static methods for getting users"""
    with app.app_context():
        # Create test user
        user = User.create_user('test@test.com', 'Test User', 'pass')
        user.approve()
        db.session.add(user)
        db.session.commit()
        
        # Test get by email
        found_user = User.get_by_email('test@test.com')
        assert found_user is not None
        assert found_user.name == 'Test User'
        
        # Test get by non-existent email
        not_found = User.get_by_email('notexist@test.com')
        assert not_found is None


def test_user_serialization(app):
    """Test user to_dict method"""
    with app.app_context():
        user = User.create_user('test@test.com', 'Test User', 'pass')
        user.approve(UserRole.MEMBER)
        
        user_dict = user.to_dict()
        
        assert user_dict['email'] == 'test@test.com'
        assert user_dict['name'] == 'Test User'
        assert user_dict['role'] == 'member'
        assert user_dict['is_approved'] is True
        assert 'created_at' in user_dict