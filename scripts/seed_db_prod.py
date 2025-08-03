#!/usr/bin/env python3
"""
Production database seeding script

This script creates minimal data required for production:
- Only admin user for system administration
- No test trips or other development data

Run with: python scripts/seed_db_prod.py
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.user import User, UserRole, db


def seed_admin_user():
    """Create admin user for production"""

    admin_data = {
        "email": "admin@pd-triglav.si",
        "name": "Administrator PD Triglav",
        "password": "password123",  # Change this in production!
        "role": UserRole.ADMIN,
        "approved": True,
    }

    # Check if admin already exists
    existing_admin = User.get_by_email(admin_data["email"])
    if existing_admin:
        print(f"✅ Admin uporabnik {admin_data['email']} že obstaja.")
        return existing_admin

    # Create new admin user
    admin = User.create_user(
        email=admin_data["email"],
        name=admin_data["name"],
        password=admin_data["password"],
        role=admin_data["role"],
    )

    if admin:
        # Approve admin user
        admin.approve(admin_data["role"])
        db.session.add(admin)

        try:
            db.session.commit()
            print(f"✅ Ustvarjen admin uporabnik: {admin.name} ({admin.email})")
            return admin
        except Exception as e:
            db.session.rollback()
            print(f"❌ Napaka pri shranjevanju admin uporabnika: {e}")
            return None
    else:
        print(f"❌ Napaka pri ustvarjanju admin uporabnika {admin_data['email']}")
        return None


def main():
    """Main production seeding function"""
    app = create_app()

    with app.app_context():
        print("🏭 Zaganjam polnjenje produkcijskih podatkov...\n")

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

        # Create admin user
        admin = seed_admin_user()

        if admin:
            print("\n🔑 Podatki za prijavo:")
            print(f"   Admin: {admin.email} / password123")
            print("\n⚠️  POMEMBNO: Spremenite geslo po prvi prijavi!")

        print("\n🚀 Produkcijska baza je pripravljena.")
        print("💡 Za zagon aplikacije uporabite: python3 app.py")


if __name__ == "__main__":
    main()
