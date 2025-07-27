"""Test historical events routes and integration"""

import pytest
from unittest.mock import patch, Mock
from flask import url_for
from models.content import HistoricalEvent, EventCategory
from models.user import db, UserRole


class TestHomepageHistoricalEvents:
    """Test historical events integration on homepage"""
    
    @pytest.fixture
    def sample_event(self, app):
        """Create sample historical event"""
        with app.app_context():
            event = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Test Historical Event',
                description='A significant test event in mountaineering history.',
                location='Test Mountain Range',
                people=['Test Climber', 'Test Guide'],
                url='https://example.com/source1',
                url_secondary='https://example.com/source2',
                category=EventCategory.FIRST_ASCENT,
                methodology='Direct date search',
                url_methodology='Verified through primary sources',
                is_featured=True,
                is_generated=True
            )
            db.session.add(event)
            db.session.commit()
            return event
    
    def test_homepage_shows_historical_events_for_authenticated_users(self, client, test_users, sample_event):
        """Test that authenticated users see historical events section"""
        # Login as member
        response = client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        assert response.status_code == 302  # Redirect after login
        
        # Mock today's date to match sample event
        with patch('models.content.datetime') as mock_datetime:
            from datetime import datetime
            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime
            
            response = client.get('/')
            assert response.status_code == 200
            
            # Should contain historical events section
            assert b'Na ta dan v zgodovini' in response.data
            assert b'Test Historical Event' in response.data
            assert b'Test Mountain Range' in response.data
            assert b'Test Climber' in response.data
            assert b'Vir 1' in response.data  # Source link
            assert b'Vir 2' in response.data  # Secondary source link
    
    def test_homepage_shows_historical_events_for_all_users_temp(self, client, sample_event):
        """Test that all users see historical events (temporary for testing)"""
        # Note: This test reflects current temporary state where everyone sees events
        
        # Mock today's date to match sample event
        with patch('models.content.datetime') as mock_datetime:
            from datetime import datetime
            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime
            
            response = client.get('/')
            assert response.status_code == 200
            
            # Should contain historical events section even without login
            assert b'Na ta dan v zgodovini' in response.data
            assert b'Test Historical Event' in response.data
    
    def test_homepage_generates_event_when_none_exists(self, client, test_users):
        """Test event generation when no event exists for today"""
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        mock_generated_event = Mock()
        mock_generated_event.title = 'Generated Test Event'
        mock_generated_event.date = '27 July'
        mock_generated_event.year = 1953
        mock_generated_event.description = 'Generated description'
        mock_generated_event.location = 'Generated Location'
        mock_generated_event.people_list = ['Generated Person']
        mock_generated_event.url = 'https://generated.com'
        mock_generated_event.url_secondary = None
        mock_generated_event.category.value = 'first_ascent'
        mock_generated_event.is_generated = True
        mock_generated_event.created_at.strftime.return_value = '27. 7. 2024'
        
        with patch('routes.main.HistoricalEvent') as mock_model:
            mock_model.get_todays_event.return_value = None  # No existing event
            
            with patch('routes.main.generate_todays_historical_event') as mock_generate:
                mock_generate.return_value = mock_generated_event
                
                response = client.get('/')
                assert response.status_code == 200
                
                # Should trigger generation and display the generated event
                mock_model.get_todays_event.assert_called_once()
                mock_generate.assert_called_once()
    
    def test_homepage_handles_event_generation_error(self, client, test_users):
        """Test graceful handling of event generation errors"""
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        with patch('routes.main.HistoricalEvent') as mock_model:
            mock_model.get_todays_event.return_value = None
            
            with patch('routes.main.generate_todays_historical_event') as mock_generate:
                mock_generate.side_effect = Exception("Generation failed")
                
                response = client.get('/')
                assert response.status_code == 200
                
                # Should not crash, should continue without historical event
                # No historical events section should be shown
                # Note: This behavior depends on the error handling implementation
    
    def test_homepage_event_display_formatting(self, client, test_users, sample_event):
        """Test proper formatting of historical event display"""
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        with patch('models.content.datetime') as mock_datetime:
            from datetime import datetime
            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime
            
            response = client.get('/')
            assert response.status_code == 200
            
            # Check for proper HTML structure
            assert b'card border-primary' in response.data  # Main card
            assert b'card-header bg-primary text-white' in response.data  # Header
            assert b'27 July, 1953' in response.data  # Full date string
            assert b'badge bg-success' in response.data  # Category badge for first_ascent
            assert b'Prva vzpon' in response.data  # Slovenian category text
            assert b'bi bi-mountain' in response.data  # Category icon
            assert b'avtomatsko generirana' in response.data  # Generation indicator
    
    def test_homepage_event_category_badges_and_icons(self, client, test_users, app):
        """Test different category badges and icons"""
        # Test each category type
        categories = [
            (EventCategory.FIRST_ASCENT, 'bg-success', 'Prva vzpon', 'bi-mountain'),
            (EventCategory.ACHIEVEMENT, 'bg-warning', 'Dosežek', 'bi-trophy'),
            (EventCategory.EXPEDITION, 'bg-info', 'Odprava', 'bi-compass'),
            (EventCategory.DISCOVERY, 'bg-secondary', 'Odkritje', 'bi-search'),
            (EventCategory.TRAGEDY, 'bg-danger', 'Tragedija', 'bi-heart'),
        ]
        
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        for category, badge_class, slovenian_text, icon_class in categories:
            with app.app_context():
                # Clear existing events
                HistoricalEvent.query.delete()
                
                # Create event with specific category
                event = HistoricalEvent(
                    date='27 July',
                    year=1953,
                    title=f'Test {category.value} Event',
                    description='Test description',
                    category=category
                )
                db.session.add(event)
                db.session.commit()
                
                with patch('models.content.datetime') as mock_datetime:
                    from datetime import datetime
                    mock_datetime.now.return_value = datetime(2024, 7, 27)
                    mock_datetime.strftime = datetime.strftime
                    
                    response = client.get('/')
                    assert response.status_code == 200
                    
                    # Check for category-specific elements
                    assert badge_class.encode() in response.data
                    assert slovenian_text.encode() in response.data
                    assert icon_class.encode() in response.data
    
    def test_homepage_dual_url_display(self, client, test_users, app):
        """Test display of dual URLs when available"""
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        with app.app_context():
            # Test event with both URLs
            event_both = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Event with Both URLs',
                description='Test description',
                url='https://source1.com',
                url_secondary='https://source2.com',
                category=EventCategory.FIRST_ASCENT
            )
            db.session.add(event_both)
            db.session.commit()
            
            with patch('models.content.datetime') as mock_datetime:
                from datetime import datetime
                mock_datetime.now.return_value = datetime(2024, 7, 27)
                mock_datetime.strftime = datetime.strftime
                
                response = client.get('/')
                assert response.status_code == 200
                
                # Should show both source buttons
                assert b'Vir 1' in response.data
                assert b'Vir 2' in response.data
                assert b'https://source1.com' in response.data
                assert b'https://source2.com' in response.data
                
        with app.app_context():
            # Clear and test event with only primary URL
            HistoricalEvent.query.delete()
            
            event_single = HistoricalEvent(
                date='27 July',
                year=1953,
                title='Event with Single URL',
                description='Test description',
                url='https://source1.com',
                url_secondary=None,
                category=EventCategory.FIRST_ASCENT
            )
            db.session.add(event_single)
            db.session.commit()
            
            with patch('models.content.datetime') as mock_datetime:
                from datetime import datetime
                mock_datetime.now.return_value = datetime(2024, 7, 27)
                mock_datetime.strftime = datetime.strftime
                
                response = client.get('/')
                assert response.status_code == 200
                
                # Should show only primary source button
                assert b'Vir 1' in response.data
                assert b'Vir 2' not in response.data


class TestFutureAdminRoutes:
    """Test future admin routes for historical events management"""
    
    def test_admin_regenerate_route_placeholder(self, client, test_users):
        """Test that admin regenerate route doesn't exist yet"""
        # Login as admin
        client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'adminpass'
        })
        
        # Try to access future admin regenerate route
        response = client.post('/admin/regenerate-today-event')
        assert response.status_code == 404  # Should not exist yet
    
    def test_admin_permissions_checking_placeholder(self, client, test_users):
        """Test that admin permission checking will be needed"""
        # Login as regular member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        # Future admin routes should check permissions
        # This is a placeholder test for when admin routes are implemented
        pass


class TestFutureHistoryArchiveRoutes:
    """Test future history archive routes"""
    
    def test_history_archive_route_placeholder(self, client):
        """Test that history archive route doesn't exist yet"""
        response = client.get('/history/')
        assert response.status_code == 404  # Should not exist yet
    
    def test_history_event_detail_route_placeholder(self, client):
        """Test that event detail route doesn't exist yet"""
        response = client.get('/history/event/1')
        assert response.status_code == 404  # Should not exist yet
    
    def test_history_load_more_api_placeholder(self, client):
        """Test that load more API doesn't exist yet"""
        response = client.get('/history/api/load-more')
        assert response.status_code == 404  # Should not exist yet


class TestAuthenticationRequirements:
    """Test authentication requirements for historical events"""
    
    def test_historical_events_authentication_current(self, client, sample_event):
        """Test current authentication requirements"""
        # Note: Currently set to show to everyone for testing
        # This test documents the current temporary state
        
        with patch('models.content.datetime') as mock_datetime:
            from datetime import datetime
            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime
            
            # Should show to unauthenticated users (temporary)
            response = client.get('/')
            assert response.status_code == 200
            assert b'Na ta dan v zgodovini' in response.data
    
    def test_pending_user_access(self, client, test_users, sample_event):
        """Test access for pending users"""
        # Login as pending user
        client.post('/auth/login', data={
            'email': 'pending@test.com',
            'password': 'pendingpass'
        })
        
        with patch('models.content.datetime') as mock_datetime:
            from datetime import datetime
            mock_datetime.now.return_value = datetime(2024, 7, 27)
            mock_datetime.strftime = datetime.strftime
            
            response = client.get('/')
            assert response.status_code == 200
            
            # Currently shows to everyone, but future implementation
            # might restrict to approved members only


class TestErrorHandling:
    """Test error handling in historical events routes"""
    
    def test_database_error_handling(self, client, test_users):
        """Test handling of database errors"""
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        with patch('routes.main.HistoricalEvent') as mock_model:
            mock_model.get_todays_event.side_effect = Exception("Database error")
            
            response = client.get('/')
            assert response.status_code == 200
            
            # Should handle error gracefully and not crash
            # Page should still load without historical events section
    
    def test_template_rendering_with_none_event(self, client, test_users):
        """Test template rendering when no event is available"""
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        with patch('routes.main.HistoricalEvent') as mock_model:
            mock_model.get_todays_event.return_value = None
            
            with patch('routes.main.generate_todays_historical_event') as mock_generate:
                mock_generate.return_value = None
                
                response = client.get('/')
                assert response.status_code == 200
                
                # Should show fallback content or hide section
                # Check that page renders without errors


class TestPerformanceConsiderations:
    """Test performance aspects of historical events routes"""
    
    def test_single_database_query_for_todays_event(self, client, test_users, sample_event):
        """Test that only one database query is made for today's event"""
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        with patch('models.content.HistoricalEvent.get_todays_event') as mock_get:
            mock_get.return_value = sample_event
            
            response = client.get('/')
            assert response.status_code == 200
            
            # Should only call get_todays_event once
            mock_get.assert_called_once()
    
    def test_no_unnecessary_generation_calls(self, client, test_users, sample_event):
        """Test that generation is not called when event exists"""
        # Login as member
        client.post('/auth/login', data={
            'email': 'member@test.com',
            'password': 'memberpass'
        })
        
        with patch('models.content.HistoricalEvent.get_todays_event') as mock_get:
            mock_get.return_value = sample_event
            
            with patch('routes.main.generate_todays_historical_event') as mock_generate:
                response = client.get('/')
                assert response.status_code == 200
                
                # Should not call generation when event already exists
                mock_generate.assert_not_called()