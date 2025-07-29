"""Test database seeding functionality"""

import pytest
import subprocess
import sys
import os
from models.user import User, UserRole, db
from models.trip import Trip

# Helper function to get script path
def get_seed_script_path():
    """Get the path to the seed_db.py script"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'seed_db.py')


# Mark as integration test since it tests the actual seeding script
pytestmark = [pytest.mark.integration]


class TestDatabaseSeeding:
    """Test the database seeding script functionality"""
    
    def test_seed_script_creates_test_users(self, app):
        """Test that seed_db.py creates the expected 4 test users"""
        with app.app_context():
            # Verify database is initially empty
            initial_user_count = User.query.count()
            assert initial_user_count == 0, "Database should be empty before seeding"
            
            # Get the test database URI from app config  
            test_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            
            # Run the seeding script with test database
            env = os.environ.copy()
            env['DATABASE_URL'] = test_db_uri
            
            result = subprocess.run([
                sys.executable, get_seed_script_path()
            ], capture_output=True, text=True, env=env)
            
            # Verify script executed successfully
            assert result.returncode == 0, f"Seeding script failed: {result.stderr}"
            
            # Check that 4 users were created
            user_count = User.query.count()
            assert user_count == 4, f"Expected 4 users, found {user_count}"
    
    def test_seed_users_have_correct_roles_and_data(self, app):
        """Test that seeded users have correct roles and properties"""
        with app.app_context():
            # Run seeding if not already done
            if User.query.count() == 0:
                test_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
                env = os.environ.copy()
                env['DATABASE_URL'] = test_db_uri
                subprocess.run([sys.executable, get_seed_script_path()], capture_output=True, env=env)
            
            # Test admin user
            admin = User.query.filter_by(email='admin@pd-triglav.si').first()
            assert admin is not None, "Admin user not found"
            assert admin.role == UserRole.ADMIN, f"Admin has wrong role: {admin.role}"
            assert admin.is_approved == True, "Admin should be approved"
            assert admin.check_password('password123'), "Admin password incorrect"
            
            # Test member user  
            member = User.query.filter_by(email='clan@pd-triglav.si').first()
            assert member is not None, "Member user not found"
            assert member.role == UserRole.MEMBER, f"Member has wrong role: {member.role}"
            assert member.is_approved == True, "Member should be approved"
            assert member.check_password('password123'), "Member password incorrect"
            
            # Test trip leader user
            trip_leader = User.query.filter_by(email='vodnik@pd-triglav.si').first()
            assert trip_leader is not None, "Trip leader user not found"
            assert trip_leader.role == UserRole.TRIP_LEADER, f"Trip leader has wrong role: {trip_leader.role}"
            assert trip_leader.is_approved == True, "Trip leader should be approved"
            assert trip_leader.check_password('password123'), "Trip leader password incorrect"
            
            # Test pending user
            pending = User.query.filter_by(email='pending@pd-triglav.si').first()
            assert pending is not None, "Pending user not found"
            assert pending.role == UserRole.PENDING, f"Pending user has wrong role: {pending.role}"
            assert pending.is_approved == False, "Pending user should not be approved"
            assert pending.check_password('password123'), "Pending user password incorrect"
    
    def test_seed_users_meet_password_requirements(self, app):
        """Test that seeded users meet our security password requirements"""
        with app.app_context():
            if User.query.count() == 0:
                test_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
                env = os.environ.copy()
                env['DATABASE_URL'] = test_db_uri
                subprocess.run([sys.executable, get_seed_script_path()], 
                             capture_output=True, env=env)
            
            test_emails = [
                'admin@pd-triglav.si',
                'clan@pd-triglav.si', 
                'vodnik@pd-triglav.si',
                'pending@pd-triglav.si'
            ]
            
            for email in test_emails:
                user = User.query.filter_by(email=email).first()
                assert user is not None, f"User {email} not found"
                
                # Test that password meets our 8+ character requirement
                # We can't test the actual password hash, but we can verify it was set
                assert user.password_hash is not None, f"User {email} has no password hash"
                assert len(user.password_hash) > 0, f"User {email} has empty password hash"
                
                # Test that the known password works (8+ characters)
                assert user.check_password('password123'), f"User {email} password verification failed"
    
    def test_seed_script_creates_sample_trips(self, app):
        """Test that seeding script creates sample trips for testing"""
        with app.app_context():
            if User.query.count() == 0:
                test_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
                env = os.environ.copy()
                env['DATABASE_URL'] = test_db_uri
                subprocess.run([sys.executable, get_seed_script_path()], 
                             capture_output=True, env=env)
            
            # Check that trips were created
            trip_count = Trip.query.count()
            assert trip_count >= 4, f"Expected at least 4 trips, found {trip_count}"
            
            # Verify some expected trip titles exist
            expected_trips = [
                'Triglav - kraljica slovenskih gora',
                'Mangart - razgled v tri države'
            ]
            
            for trip_title in expected_trips:
                trip = Trip.query.filter(Trip.title.contains(trip_title.split(' - ')[0])).first()
                assert trip is not None, f"Expected trip '{trip_title}' not found"
    
    def test_seed_script_idempotent(self, app):
        """Test that running seed script multiple times doesn't create duplicates"""
        with app.app_context():
            # Run seeding script twice
            test_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            env = os.environ.copy()
            env['DATABASE_URL'] = test_db_uri
            subprocess.run([sys.executable, get_seed_script_path()], 
                         capture_output=True, env=env)
            
            first_user_count = User.query.count()
            first_trip_count = Trip.query.count()
            
            # Run again
            test_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            env = os.environ.copy()
            env['DATABASE_URL'] = test_db_uri
            result = subprocess.run([sys.executable, get_seed_script_path()], 
                                  capture_output=True, text=True, env=env)
            
            # Should still have same counts (no duplicates)
            second_user_count = User.query.count()
            second_trip_count = Trip.query.count()
            
            assert second_user_count == first_user_count, "Seeding created duplicate users"
            assert second_trip_count == first_trip_count, "Seeding created duplicate trips"
            
            # Script should handle duplicates gracefully
            assert result.returncode == 0, f"Second seeding run failed: {result.stderr}"


class TestUserRoleHelperMethods:
    """Test user role helper methods work correctly with seeded data"""
    
    def test_user_role_helper_methods(self, app):
        """Test is_admin(), is_member(), etc. methods work correctly"""
        with app.app_context():
            if User.query.count() == 0:
                test_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
                env = os.environ.copy()
                env['DATABASE_URL'] = test_db_uri
                subprocess.run([sys.executable, get_seed_script_path()], 
                             capture_output=True, env=env)
            
            # Test admin user methods
            admin = User.query.filter_by(email='admin@pd-triglav.si').first()
            assert admin.is_admin() == True, "Admin user is_admin() should return True"
            assert admin.is_member() == True, "Admin user is_member() should return True"
            assert admin.is_trip_leader() == True, "Admin user is_trip_leader() should return True"
            assert admin.is_pending() == False, "Admin user is_pending() should return False"
            
            # Test member user methods
            member = User.query.filter_by(email='clan@pd-triglav.si').first()
            assert member.is_admin() == False, "Member user is_admin() should return False"
            assert member.is_member() == True, "Member user is_member() should return True"
            assert member.is_trip_leader() == False, "Member user is_trip_leader() should return False"
            assert member.is_pending() == False, "Member user is_pending() should return False"
            
            # Test trip leader methods
            trip_leader = User.query.filter_by(email='vodnik@pd-triglav.si').first()
            assert trip_leader.is_admin() == False, "Trip leader is_admin() should return False"
            assert trip_leader.is_member() == True, "Trip leader is_member() should return True"
            assert trip_leader.is_trip_leader() == True, "Trip leader is_trip_leader() should return True"
            assert trip_leader.is_pending() == False, "Trip leader is_pending() should return False"
            
            # Test pending user methods
            pending = User.query.filter_by(email='pending@pd-triglav.si').first()
            assert pending.is_admin() == False, "Pending user is_admin() should return False"
            assert pending.is_member() == False, "Pending user is_member() should return False"
            assert pending.is_trip_leader() == False, "Pending user is_trip_leader() should return False"
            assert pending.is_pending() == True, "Pending user is_pending() should return True"


@pytest.mark.slow  
class TestDatabaseSeedingIntegration:
    """Slower integration tests for complete seeding workflow"""
    
    def test_complete_seeding_workflow(self, app):
        """Test the complete seeding workflow including cleanup and recreation"""
        with app.app_context():
            # Start with clean database
            db.drop_all()
            db.create_all()
            
            assert User.query.count() == 0, "Database should be empty after cleanup"
            assert Trip.query.count() == 0, "Database should be empty after cleanup"
            
            # Run seeding
            test_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            env = os.environ.copy()
            env['DATABASE_URL'] = test_db_uri
            result = subprocess.run([sys.executable, get_seed_script_path()], 
                                  capture_output=True, text=True, env=env)
            
            assert result.returncode == 0, f"Seeding failed: {result.stderr}"
            
            # Verify complete setup
            assert User.query.count() == 4, "Should have 4 users after seeding"
            assert Trip.query.count() >= 4, "Should have at least 4 trips after seeding"
            
            # Verify all users can authenticate
            test_users = [
                ('admin@pd-triglav.si', UserRole.ADMIN),
                ('clan@pd-triglav.si', UserRole.MEMBER),
                ('vodnik@pd-triglav.si', UserRole.TRIP_LEADER),
                ('pending@pd-triglav.si', UserRole.PENDING)
            ]
            
            for email, expected_role in test_users:
                user = User.query.filter_by(email=email).first()
                assert user is not None, f"User {email} not created"
                assert user.role == expected_role, f"User {email} has wrong role"
                assert user.check_password('password123'), f"User {email} password failed"