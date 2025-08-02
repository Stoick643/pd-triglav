# Database Directory

This directory contains all SQLite database files for the PD Triglav project.

## Database Files

### Development Database
- **`development.db`** - Main development database
- Contains seeded test data for manual testing
- Used when running `python3 app.py`

### Test Databases  
- **`test_main_[uuid].db`** - Test databases with unique names
- **`test_worker[N]_[uuid].db`** - Parallel test worker databases
- Created and destroyed automatically during test runs
- Completely isolated from development database

## Database Lifecycle

### Development
```bash
# Initialize/upgrade database schema
flask db upgrade

# Seed with test data
python3 scripts/seed_db.py

# Start development server
python3 app.py
```

### Testing
```bash
# Run tests (automatically manages test databases)
pytest

# Tests create isolated databases and clean them up
# Each test gets a fresh, isolated database
```

## Git Policy

- **Directory structure** is tracked in git (via `.gitkeep`)
- **Database files** are ignored in git (via `.gitignore`)
- Each developer maintains their own local database content
- Production uses PostgreSQL (not SQLite files)

## Cleanup

Test databases are automatically cleaned up, but if needed:
```bash
# Remove all test databases
rm -f databases/test_*.db

# Reset development database
rm -f databases/development.db
flask db upgrade
python3 scripts/seed_db.py
```