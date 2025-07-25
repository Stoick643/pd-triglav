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


def main():
    """Main seeding function"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Zaganjam polnjenje testnih podatkov...\n")
        
        # Create tables if they don't exist
        db.create_all()
        print("📊 Tabele v bazi so pripravljene.")
        
        # Seed users
        seed_users()
        
        # Show current users
        print_users()
        
        print(f"\n🔑 Podatki za prijavo:")
        print("   Admin:       admin@pd-triglav.si / password123")
        print("   Član:        clan@pd-triglav.si / password123")
        print("   Vodnik:      vodnik@pd-triglav.si / password123")
        print("   Čakajoči:    pending@pd-triglav.si / password123")
        
        print("\n🚀 Za zagon aplikacije uporabite: python app.py")


if __name__ == '__main__':
    main()