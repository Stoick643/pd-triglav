"""
Migration script: Convert historical_events from string 'date' column
to structured event_month/event_day integer columns.

Run once after deploying the schema change.
Usage: python scripts/migrate_dates_to_structured.py
"""

import os
import sys
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Month name mappings (English + Slovenian)
MONTH_LOOKUP = {
    # English
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    # Slovenian
    'januar': 1, 'februar': 2, 'marec': 3,
    'maj': 5, 'junij': 6, 'julij': 7, 'avgust': 8,
    'oktober': 10,
}


def parse_old_date(date_str):
    """Parse old-format date string to (month, day)."""
    if not date_str:
        return None, None
    
    date_str = date_str.strip()
    
    # "DD Month" (e.g., "09 November", "16 February")
    match = re.match(r'^(\d{1,2})\s+([A-Za-z\u010d\u0161\u017e]+)$', date_str)
    if match:
        day = int(match.group(1))
        month_name = match.group(2).lower()
        month = MONTH_LOOKUP.get(month_name)
        if month:
            return month, day
    
    # "Month DD" (e.g., "Julij 15", "April 23")
    match = re.match(r'^([A-Za-z\u010d\u0161\u017e]+)\s+(\d{1,2})$', date_str)
    if match:
        month_name = match.group(1).lower()
        day = int(match.group(2))
        month = MONTH_LOOKUP.get(month_name)
        if month:
            return month, day
    
    return None, None


def migrate():
    """Run the migration."""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        import sqlite3
        
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_path):
            print(f"Database not found: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if old 'date' column exists
        columns = [row[1] for row in cursor.execute("PRAGMA table_info(historical_events)").fetchall()]
        
        if 'date' not in columns:
            print("No 'date' column found - migration may already be complete or table has new schema.")
            
            if 'event_month' in columns:
                print("event_month/event_day columns already exist. Migration not needed.")
                conn.close()
                return
            else:
                print("ERROR: Neither 'date' nor 'event_month' found!")
                conn.close()
                return
        
        if 'event_month' in columns:
            print("Both old and new columns exist. Checking if migration is needed...")
            # Check for NULL event_month values
            null_count = cursor.execute(
                "SELECT COUNT(*) FROM historical_events WHERE event_month IS NULL"
            ).fetchone()[0]
            if null_count == 0:
                print("All records already migrated. Done.")
                conn.close()
                return
        
        # SQLite doesn't support ADD COLUMN with constraints easily,
        # so we'll recreate the table with the new schema.
        # But first, let's try the simple approach if columns don't exist yet.
        
        if 'event_month' not in columns:
            print("Adding event_month and event_day columns...")
            cursor.execute("ALTER TABLE historical_events ADD COLUMN event_month INTEGER")
            cursor.execute("ALTER TABLE historical_events ADD COLUMN event_day INTEGER")
        
        # Read all existing records
        rows = cursor.execute("SELECT id, date FROM historical_events").fetchall()
        print(f"\nMigrating {len(rows)} records...")
        
        migrated = 0
        failed = 0
        
        for row_id, date_str in rows:
            month, day = parse_old_date(date_str)
            if month and day:
                cursor.execute(
                    "UPDATE historical_events SET event_month = ?, event_day = ? WHERE id = ?",
                    (month, day, row_id)
                )
                migrated += 1
                print(f"  OK: '{date_str}' -> month={month}, day={day}")
            else:
                failed += 1
                print(f"  FAILED: Could not parse '{date_str}' (id={row_id})")
        
        conn.commit()
        
        # Verify
        null_count = cursor.execute(
            "SELECT COUNT(*) FROM historical_events WHERE event_month IS NULL OR event_day IS NULL"
        ).fetchone()[0]
        
        print(f"\nMigration complete: {migrated} migrated, {failed} failed, {null_count} still NULL")
        
        if null_count == 0:
            print("\nAll records migrated successfully!")
            print("You can now drop the old 'date' column if desired.")
        else:
            print(f"\nWARNING: {null_count} records still have NULL month/day values!")
        
        conn.close()


if __name__ == '__main__':
    migrate()
