#!/usr/bin/env python3
"""
Remove beta test users from production.

Run on Fly.io: fly ssh console -> python scripts/remove_test_users_prod.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.user import User, db

TEST_EMAILS = [
    "clan@pd-triglav.si",
    "vodnik@pd-triglav.si",
    "pending@pd-triglav.si",
]


def main():
    app = create_app()

    with app.app_context():
        print("🧹 Odstranjujem testne uporabnike...\n")

        removed = 0
        for email in TEST_EMAILS:
            user = User.get_by_email(email)
            if user:
                db.session.delete(user)
                print(f"  🗑️  {email} ({user.name}) — odstranjen")
                removed += 1
            else:
                print(f"  ⏭️  {email} — ne obstaja, preskačem")

        if removed:
            try:
                db.session.commit()
                print(f"\n✅ Odstranjenih {removed} testnih uporabnikov.")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Napaka: {e}")
        else:
            print("\n📝 Ni testnih uporabnikov za odstraniti.")


if __name__ == "__main__":
    main()
