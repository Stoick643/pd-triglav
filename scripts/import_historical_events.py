import json
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import db
from models.content import HistoricalEvent, EventCategory
from app import create_app

def import_events_to_db(json_file_path='scraped_history.json'):
    """
    Imports historical events from a JSON file into the database.
    """
    app = create_app()
    with app.app_context():
        print(f"Starting import of historical events from {json_file_path}...")
        
        if not os.path.exists(json_file_path):
            print(f"Error: JSON file not found at {json_file_path}")
            return

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {json_file_path}: {e}")
            return
        except Exception as e:
            print(f"Error reading {json_file_path}: {e}")
            return

        events_to_import = data.get('events', [])
        if not events_to_import:
            print("No events found in the JSON file to import.")
            return

        imported_count = 0
        skipped_count = 0
        
        for event_data in events_to_import:
            date_str = event_data.get('date')
            year = event_data.get('year')
            title = event_data.get('title')

            if not all([date_str, year, title]):
                print(f"Skipping event due to missing required data: {event_data}")
                skipped_count += 1
                continue

            # Check for existing event to prevent duplicates
            existing_event = HistoricalEvent.query.filter_by(date=date_str, year=year).first()
            if existing_event:
                print(f"Skipping existing event: {title} ({date_str}, {year})")
                skipped_count += 1
                continue

            try:
                # Ensure category is a valid EventCategory enum member
                category_value = event_data.get('category', 'achievement') # Changed to lowercase
                if category_value not in [e.value for e in EventCategory]:
                    print(f"Warning: Invalid category '{category_value}' for event '{title}'. Defaulting to 'achievement'.")
                    category_value = 'achievement' # Changed to lowercase
                
                new_event = HistoricalEvent(
                    date=date_str,
                    year=int(year),  # Ensure year is integer
                    title=title,
                    description=event_data.get('description', ''),
                    location=event_data.get('location'),
                    people=event_data.get('people', []),
                    url=event_data.get('url'),
                    url_secondary=event_data.get('url_secondary'),
                    category=EventCategory(category_value),
                    methodology=event_data.get('methodology'),
                    url_methodology=event_data.get('url_methodology'),
                    is_featured=event_data.get('is_featured', False),
                    is_generated=False,  # Scraped data, not AI-generated
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(new_event)
                imported_count += 1
            except Exception as e:
                db.session.rollback()
                print(f"Error importing event '{title} ({date_str}, {year})': {e}")
                skipped_count += 1
                continue
        
        try:
            db.session.commit()
            print(f"\nImport complete. Successfully imported {imported_count} events. Skipped {skipped_count} events.")
        except Exception as e:
            db.session.rollback()
            print(f"Error during final commit: {e}")

if __name__ == '__main__':
    import_events_to_db()
