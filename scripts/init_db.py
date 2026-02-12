#!/usr/bin/env python3
"""
Database initialization script for Fly.io deployment

This script:
1. Creates all database tables from SQLAlchemy models (db.create_all)
2. Seeds the admin user if not exists

Designed to be idempotent - safe to run multiple times.
Used as Fly.io release_command before each deployment.

Run manually: python scripts/init_db.py
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.user import User, UserRole, db


def create_tables():
    """Create all database tables from SQLAlchemy models"""
    print("📊 Creating database tables...")
    db.create_all()
    print("✅ Database tables created (or already exist).")


def seed_admin_user():
    """Create admin user if not exists"""
    admin_email = "admin@pd-triglav.si"
    
    existing_admin = User.get_by_email(admin_email)
    if existing_admin:
        print(f"✅ Admin user already exists: {admin_email}")
        return existing_admin

    print(f"👤 Creating admin user: {admin_email}")
    
    admin = User.create_user(
        email=admin_email,
        name="Administrator PD Triglav",
        password="password123",  # Change this after first login!
        role=UserRole.ADMIN,
    )

    if admin:
        admin.approve(UserRole.ADMIN)
        db.session.add(admin)
        
        try:
            db.session.commit()
            print(f"✅ Admin user created: {admin.name} ({admin.email})")
            print("⚠️  IMPORTANT: Change the default password after first login!")
            return admin
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving admin user: {e}")
            return None
    else:
        print(f"❌ Error creating admin user")
        return None


def main():
    """Main initialization function"""
    print("🚀 PD Triglav - Database Initialization")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # Step 1: Create tables
        create_tables()
        
        # Step 2: Seed admin user
        seed_admin_user()
        
        print("=" * 50)
        print("✅ Database initialization complete!")


if __name__ == "__main__":
    main()
