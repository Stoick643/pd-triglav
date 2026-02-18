#!/usr/bin/env python3
"""
Create test users for beta testing on production.

Creates pre-approved users for each role so testers can log in immediately.
Run on Fly.io: fly ssh console -> python scripts/seed_test_users_prod.py

Usage:
    python scripts/seed_test_users_prod.py                    # Create all test users
    python scripts/seed_test_users_prod.py --password SECRET   # Custom password (recommended!)
"""

import sys
import os
import argparse

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.user import User, UserRole, db


def create_test_users(password="test2026!"):
    """Create test users for all roles"""

    test_users = [
        {
            "email": "clan@pd-triglav.si",
            "name": "Marko Planinski (Test Član)",
            "password": password,
            "role": UserRole.MEMBER,
        },
        {
            "email": "vodnik@pd-triglav.si",
            "name": "Ana Vodnik (Test Vodnik)",
            "password": password,
            "role": UserRole.TRIP_LEADER,
        },
        {
            "email": "pending@pd-triglav.si",
            "name": "Novo Članstvo (Test Čakajoči)",
            "password": password,
            "role": UserRole.PENDING,
        },
    ]

    created = []
    skipped = []

    for user_data in test_users:
        existing = User.get_by_email(user_data["email"])
        if existing:
            skipped.append(user_data["email"])
            print(f"  ⏭️  {user_data['email']} že obstaja, preskačem.")
            continue

        user = User.create_user(
            email=user_data["email"],
            name=user_data["name"],
            password=user_data["password"],
            role=user_data["role"],
        )

        if user:
            # Approve all except PENDING role
            if user_data["role"] != UserRole.PENDING:
                user.approve(user_data["role"])

            db.session.add(user)
            created.append(user_data)
            role_sl = {
                UserRole.MEMBER: "Član",
                UserRole.TRIP_LEADER: "Vodnik",
                UserRole.PENDING: "Čakajoči",
            }
            print(f"  ✅ {user_data['email']} — {role_sl[user_data['role']]}")

    if created:
        try:
            db.session.commit()
            print(f"\n✅ Ustvarjenih {len(created)} novih testnih uporabnikov!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Napaka pri shranjevanju: {e}")
            return False

    if skipped:
        print(f"\n⏭️  Preskočenih {len(skipped)} (že obstajajo).")

    return True


def main():
    parser = argparse.ArgumentParser(description="Ustvari testne uporabnike za beta testiranje")
    parser.add_argument(
        "--password",
        default="test2026!",
        help="Geslo za vse testne uporabnike (privzeto: test2026!)",
    )
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        print("🧪 Ustvarjam testne uporabnike za beta testiranje...\n")

        try:
            User.query.first()
        except Exception as e:
            print(f"❌ Baza podatkov ni pripravljena: {e}")
            return

        success = create_test_users(password=args.password)

        if success:
            print("\n" + "=" * 55)
            print("🔑 PODATKI ZA PRIJAVO (delite s testerji):")
            print("=" * 55)
            print(f"  🌐 https://pd-triglav.fly.dev/auth/login")
            print()
            print(f"  👤 Član:      clan@pd-triglav.si / {args.password}")
            print(f"  🏔️  Vodnik:    vodnik@pd-triglav.si / {args.password}")
            print(f"  ⏳ Čakajoči:  pending@pd-triglav.si / {args.password}")
            print()
            print("  ℹ️  Admin račun ostane nespremenjen.")
            print("=" * 55)
            print("\n⚠️  Po končanem testiranju odstranite testne račune!")


if __name__ == "__main__":
    main()
