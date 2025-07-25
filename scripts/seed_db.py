#!/usr/bin/env python3
"""
Database seeding script for development and testing

This script creates test users with different roles for development purposes.
Run with: python scripts/seed_db.py
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.user import User, UserRole, db
from models.trip import Trip, TripDifficulty, TripStatus
from datetime import date, time, timedelta


def seed_users():
    """Create test users for development"""
    
    users_to_create = [
        {
            'email': 'admin@pd-triglav.si',
            'name': 'Administrator PD Triglav',
            'password': 'password123',
            'role': UserRole.ADMIN,
            'approved': True
        },
        {
            'email': 'clan@pd-triglav.si',
            'name': 'Marko Planinski',
            'password': 'password123',
            'role': UserRole.MEMBER,
            'approved': True
        },
        {
            'email': 'vodnik@pd-triglav.si',
            'name': 'Ana Vodnik',
            'password': 'password123',
            'role': UserRole.TRIP_LEADER,
            'approved': True
        },
        {
            'email': 'pending@pd-triglav.si',
            'name': 'Novo Članstvo',
            'password': 'password123',
            'role': UserRole.PENDING,
            'approved': False
        }
    ]
    
    created_count = 0
    
    for user_data in users_to_create:
        # Check if user already exists
        existing_user = User.get_by_email(user_data['email'])
        if existing_user:
            print(f"Uporabnik {user_data['email']} že obstaja, preskačem...")
            continue
        
        # Create new user
        user = User.create_user(
            email=user_data['email'],
            name=user_data['name'],
            password=user_data['password'],
            role=user_data['role']
        )
        
        if user:
            # Set approval status
            if user_data['approved']:
                user.approve(user_data['role'])
            
            db.session.add(user)
            created_count += 1
            print(f"Ustvarjen uporabnik: {user.name} ({user.email}) - {user.role.value}")
        else:
            print(f"Napaka pri ustvarjanju uporabnika {user_data['email']}")
    
    if created_count > 0:
        try:
            db.session.commit()
            print(f"\n✅ Uspešno ustvarjenih {created_count} uporabnikov!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Napaka pri shranjevanju v bazo: {e}")
    else:
        print("\n📝 Vsi testni uporabniki že obstajajo.")


def seed_trips():
    """Create sample trips for development"""
    
    # Get trip leaders
    trip_leader = User.query.filter_by(email='vodnik@pd-triglav.si').first()
    admin = User.query.filter_by(email='admin@pd-triglav.si').first()
    
    if not trip_leader or not admin:
        print("⚠️  Vodniki niso najdeni, preskačem ustvarjanje izletov.")
        return
    
    # Sample trips to create
    trips_to_create = [
        {
            'title': 'Triglav - kraljica slovenskih gora',
            'description': 'Vzpon na najvišji vrh Slovenije preko Kredarice. Zahteven, a nepozaben vzpon.',
            'destination': 'Triglav (2864 m)',
            'trip_date': date.today() + timedelta(days=14),
            'meeting_time': time(6, 0),
            'meeting_point': 'Pokljuka - Rudno polje',
            'return_time': time(18, 0),
            'difficulty': TripDifficulty.EXPERT,
            'max_participants': 8,
            'equipment_needed': 'Čelada, plezalni pas, via ferrata komplet, planinska oprema',
            'cost_per_person': 25.0,
            'leader_id': trip_leader.id
        },
        {
            'title': 'Mangart - razgled v tri države',
            'description': 'Vzpon na tretji najvišji vrh Slovenije z avtom do sedla in nato peš do vrha.',
            'destination': 'Mangart (2679 m)',
            'trip_date': date.today() + timedelta(days=21),
            'meeting_time': time(7, 0),
            'meeting_point': 'Bovec - glavni trg',
            'return_time': time(17, 0),
            'difficulty': TripDifficulty.MODERATE,
            'max_participants': 12,
            'equipment_needed': 'Planinska oprema, dobra obutev',
            'cost_per_person': 15.0,
            'leader_id': admin.id
        },
        {
            'title': 'Vogel - zimski izlet',
            'description': 'Sproščen zimski izlet na Vogel z žičnico in nato do vrha.',
            'destination': 'Vogel (1922 m)',
            'trip_date': date.today() + timedelta(days=7),
            'meeting_time': time(8, 30),
            'meeting_point': 'Bohinjska Bistrica - železniška postaja',
            'return_time': time(16, 0),
            'difficulty': TripDifficulty.EASY,
            'max_participants': 15,
            'equipment_needed': 'Zimska planinska oprema, dereze',
            'cost_per_person': 35.0,
            'leader_id': trip_leader.id
        },
        {
            'title': 'Špik - tehnični izziv',
            'description': 'Zahteven vzpon preko Ruske smeri na enega najlepših vrhov v Julijskih Alpah.',
            'destination': 'Špik (2472 m)',
            'trip_date': date.today() + timedelta(days=28),
            'meeting_time': time(5, 30),
            'meeting_point': 'Kranjska Gora - center',
            'return_time': time(19, 0),
            'difficulty': TripDifficulty.DIFFICULT,
            'max_participants': 6,
            'equipment_needed': 'Polna plezalna oprema, čelada, plezalke',
            'cost_per_person': 20.0,
            'leader_id': admin.id
        }
    ]
    
    created_count = 0
    
    for trip_data in trips_to_create:
        # Check if trip already exists
        existing_trip = Trip.query.filter_by(
            title=trip_data['title'],
            trip_date=trip_data['trip_date']
        ).first()
        
        if existing_trip:
            print(f"Izlet '{trip_data['title']}' že obstaja, preskačem...")
            continue
        
        # Create new trip
        trip = Trip(**trip_data)
        db.session.add(trip)
        created_count += 1
        print(f"Ustvarjen izlet: {trip.title} ({trip.trip_date})")
    
    if created_count > 0:
        try:
            db.session.commit()
            print(f"\n✅ Uspešno ustvarjenih {created_count} izletov!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Napaka pri shranjevanju izletov: {e}")
    else:
        print("\n📝 Vsi testni izleti že obstajajo.")


def print_users():
    """Print all users in database"""
    users = User.query.all()
    
    if not users:
        print("Ni uporabnikov v bazi.")
        return
    
    print("\n📋 Trenutni uporabniki v bazi:")
    print("-" * 60)
    for user in users:
        status = "✅ Odobren" if user.is_approved else "⏳ Čaka odobritev"
        print(f"{user.name:<20} | {user.email:<25} | {user.role.value:<12} | {status}")


def print_trips():
    """Print all trips in database"""
    trips = Trip.query.all()
    
    if not trips:
        print("Ni izletov v bazi.")
        return
    
    print("\n🏔️  Trenutni izleti v bazi:")
    print("-" * 80)
    for trip in trips:
        status_icon = "📅" if trip.status == TripStatus.ANNOUNCED else "✅" if trip.status == TripStatus.COMPLETED else "❌"
        print(f"{status_icon} {trip.title:<30} | {trip.trip_date} | {trip.difficulty.slovenian_name} | Vodnik: {trip.leader.name}")


def main():
    """Main seeding function"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Zaganjam polnjenje testnih podatkov...\n")
        
        # Check if database is initialized
        try:
            # Try to query users table to check if migrations are applied
            User.query.first()
            print("📊 Baza podatkov je pripravljena (Flask-Migrate).")
        except Exception as e:
            print("❌ Baza podatkov ni inicializirana!")
            print("   Prosim zaženite: flask db upgrade")
            print(f"   Napaka: {e}")
            return
        
        # Seed users first
        seed_users()
        
        # Seed trips (depends on users)
        seed_trips()
        
        # Show current data
        print_users()
        print_trips()
        
        print(f"\n🔑 Podatki za prijavo:")
        print("   Admin:       admin@pd-triglav.si / password123")
        print("   Član:        clan@pd-triglav.si / password123")
        print("   Vodnik:      vodnik@pd-triglav.si / password123")
        print("   Čakajoči:    pending@pd-triglav.si / password123")
        
        print("\n🚀 Za zagon aplikacije uporabite: python3 app.py")
        print("💡 Za upravljanje baze uporabite: flask db migrate, flask db upgrade")


if __name__ == '__main__':
    main()