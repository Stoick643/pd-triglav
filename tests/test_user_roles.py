import pytest
from models.user import User, UserRole, db

def test_is_pending_method(app, test_users):
    """Test that is_pending() correctly identifies pending users."""
    with app.app_context():
        pending_user = test_users['pending']
        member_user = test_users['member']
        admin_user = test_users['admin']

        assert pending_user.is_pending() is True
        assert member_user.is_pending() is False
        assert admin_user.is_pending() is False

def test_is_member_method(app, test_users):
    """Test that is_member() correctly identifies approved members, leaders, and admins."""
    with app.app_context():
        pending_user = test_users['pending']
        member_user = test_users['member']
        trip_leader_user = test_users['trip_leader']
        admin_user = test_users['admin']

        assert pending_user.is_member() is False
        assert member_user.is_member() is True
        assert trip_leader_user.is_member() is True
        assert admin_user.is_member() is True

def test_is_trip_leader_method(app, test_users):
    """Test that is_trip_leader() correctly identifies trip leaders and admins."""
    with app.app_context():
        member_user = test_users['member']
        trip_leader_user = test_users['trip_leader']
        admin_user = test_users['admin']

        assert member_user.is_trip_leader() is False
        assert trip_leader_user.is_trip_leader() is True
        assert admin_user.is_trip_leader() is True

def test_is_admin_method(app, test_users):
    """Test that is_admin() correctly identifies admin users."""
    with app.app_context():
        member_user = test_users['member']
        trip_leader_user = test_users['trip_leader']
        admin_user = test_users['admin']

        assert member_user.is_admin() is False
        assert trip_leader_user.is_admin() is False
        assert admin_user.is_admin() is True

def test_user_approval_process(app):
    """Test that a pending user can be approved and their role updated."""
    with app.app_context():
        user = User.create_user('approve@test.com', 'Approve User', 'password')
        db.session.add(user)
        db.session.commit()

        assert user.is_approved is False
        assert user.role == UserRole.PENDING

        user.approve(UserRole.MEMBER)
        db.session.commit()

        assert user.is_approved is True
        assert user.role == UserRole.MEMBER

        # Test promoting to leader
        user.promote_to_trip_leader()
        db.session.commit()
        assert user.role == UserRole.TRIP_LEADER

        # Test promoting to admin
        user.promote_to_admin()
        db.session.commit()
        assert user.role == UserRole.ADMIN

def test_user_rejection_process(app):
    """Test that an approved user can be reverted to pending status."""
    with app.app_context():
        user = User.create_user('reject@test.com', 'Reject User', 'password')
        db.session.add(user)
        user.approve(UserRole.MEMBER) # Approve first
        db.session.commit()

        assert user.is_approved is True
        assert user.role == UserRole.MEMBER

        user.reject()
        db.session.commit()

        assert user.is_approved is False
        assert user.role == UserRole.PENDING
