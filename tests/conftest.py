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


@pytest.fixture
def sample_historical_events(app):
    """Create sample historical events for testing"""
    from models.content import HistoricalEvent, EventCategory
    from models.user import db
    
    def _get_events():
        """Function to get fresh event instances from database"""
        return {
            'everest': HistoricalEvent.query.filter_by(title='Mount Everest First Ascent').first(),
            'matterhorn': HistoricalEvent.query.filter_by(title='Matterhorn Tragedy').first(),
            'eiger': HistoricalEvent.query.filter_by(title='Eiger North Face Conquest').first(),
            'alpine_discovery': HistoricalEvent.query.filter_by(title='Alpine Route Discovery').first()
        }
    
    with app.app_context():
        # Check if events already exist
        if HistoricalEvent.query.filter_by(title='Mount Everest First Ascent').first():
            return _get_events()
        
        # Create sample historical events
        events = [
            HistoricalEvent(
                date='29 May',
                year=1953,
                title='Mount Everest First Ascent',
                description='Edmund Hillary and Tenzing Norgay achieve the first confirmed ascent of Mount Everest, marking a pivotal moment in mountaineering history.',
                location='Mount Everest, Nepal-Tibet border',
                people=['Edmund Hillary', 'Tenzing Norgay'],
                url='https://en.wikipedia.org/wiki/1953_British_Mount_Everest_expedition',
                url_secondary='https://www.bbc.com/news/world-asia-22637401',
                category=EventCategory.FIRST_ASCENT,
                methodology='Direct date search',
                url_methodology='Wikipedia primary source and BBC historical coverage',
                is_featured=True,
                is_generated=True
            ),
            HistoricalEvent(
                date='14 July',
                year=1865,
                title='Matterhorn Tragedy',
                description='Edward Whymper\'s team achieves the first ascent of the Matterhorn, but tragedy strikes on the descent when four team members fall to their deaths.',
                location='Matterhorn, Swiss-Italian Alps',
                people=['Edward Whymper', 'Charles Hudson', 'Lord Francis Douglas', 'Douglas Hadow'],
                url='https://en.wikipedia.org/wiki/Matterhorn#First_ascent',
                category=EventCategory.TRAGEDY,
                methodology='Historical records search',
                url_methodology='Well-documented historical event with multiple sources',
                is_featured=True,
                is_generated=True
            ),
            HistoricalEvent(
                date='24 July',
                year=1938,
                title='Eiger North Face Conquest',
                description='Anderl Heckmair, Ludwig Vörg, Heinrich Harrer, and Fritz Kasparek complete the first ascent of the notorious Eiger North Face after a dramatic four-day climb.',
                location='Eiger North Face, Swiss Alps',
                people=['Anderl Heckmair', 'Ludwig Vörg', 'Heinrich Harrer', 'Fritz Kasparek'],
                url='https://en.wikipedia.org/wiki/Eiger#North_Face',
                category=EventCategory.FIRST_ASCENT,
                methodology='Multi-day event search',
                url_methodology='Historical mountaineering records',
                is_featured=False,
                is_generated=True
            ),
            HistoricalEvent(
                date='15 August',
                year=1960,
                title='Alpine Route Discovery',
                description='A new challenging route is discovered in the Mont Blanc massif, opening up possibilities for modern alpine climbing techniques.',
                location='Mont Blanc massif, French Alps',
                people=['Alpine Pioneer'],
                url=None,
                category=EventCategory.DISCOVERY,
                methodology='Regional climbing history search',
                url_methodology=None,
                is_featured=False,
                is_generated=True
            ),
            HistoricalEvent(
                date='27 July',
                year=1953,
                title='K2 Expedition Preparation',
                description='The Italian expedition team led by Ardito Desio begins final preparations for their historic attempt on K2, which would succeed the following year.',
                location='K2 Base Camp, Pakistan',
                people=['Ardito Desio'],
                url='https://en.wikipedia.org/wiki/1954_Italian_Karakoram_expedition_to_K2',
                category=EventCategory.EXPEDITION,
                methodology='Expedition timeline research',
                url_methodology='Italian expedition historical records',
                is_featured=False,
                is_generated=True
            )
        ]
        
        for event in events:
            db.session.add(event)
        
        db.session.commit()
        
        return _get_events()


@pytest.fixture
def mock_llm_responses():
    """Provide mock LLM API responses for testing"""
    return {
        'successful_response': {
            'year': 1953,
            'title': 'Mock Historical Event',
            'description': 'A mock event generated for testing purposes.',
            'location': 'Mock Mountain Range',
            'people': ['Mock Climber', 'Mock Guide'],
            'url_1': 'https://mock.example.com/source1',
            'url_2': 'https://mock.example.com/source2',
            'category': 'first_ascent',
            'methodology': 'Mock methodology',
            'url_methodology': 'Mock source verification'
        },
        'minimal_response': {
            'year': 1965,
            'title': 'Minimal Mock Event',
            'description': 'Minimal mock event for testing.',
            'location': 'Mock Location',
            'people': ['Mock Person'],
            'category': 'achievement'
        },
        'invalid_category_response': {
            'year': 1970,
            'title': 'Invalid Category Event',
            'description': 'Event with invalid category for testing.',
            'location': 'Test Location',
            'people': ['Test Person'],
            'category': 'invalid_category'
        },
        'people_string_response': {
            'year': 1980,
            'title': 'String People Event',
            'description': 'Event with people as string for testing.',
            'location': 'String Location',
            'people': 'Person One, Person Two, Person Three',
            'category': 'expedition'
        }
    }