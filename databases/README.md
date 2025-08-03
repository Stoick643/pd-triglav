# Database Directory

This directory contains all SQLite database files for the PD Triglav project.

## Database Files

### Development Database
- **`development.db`** - Main development database
- Contains seeded test data for manual testing
- Used when running `python3 app.py`

### Test Databases
- **Hybrid Strategy**: Auto-detects single vs parallel testing mode
- **Single Mode** (`pytest`): Uses `test.db` for optimal performance
- **Parallel Mode** (`pytest -n`): Uses worker-specific databases (`test_gw0.db`, `test_gw1.db`, etc.)
- Tables are cleaned between tests (data removed, schema preserved)
- Much faster than creating/destroying databases
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
# Run tests in single mode (uses test.db)
pytest

# Run tests in parallel mode (uses test_gw0.db, test_gw1.db, etc.)
pytest -n 4

# Hybrid database strategy automatically detects mode
# Single mode: optimal performance with shared database
# Parallel mode: isolated databases per worker for reliability
```

## Git Policy

- **Directory structure** is tracked in git (via `.gitkeep`)
- **Database files** are ignored in git (via `.gitignore`)
- Each developer maintains their own local database content
- Production uses PostgreSQL (not SQLite files)

## Cleanup

Database cleanup options:
```bash
# Remove test databases (all)
rm -f databases/test*.db

# Reset development database
rm -f databases/development.db
flask db upgrade
python3 scripts/seed_db.py

# Reset all databases
rm -f databases/test*.db databases/development.db
flask db upgrade
python3 scripts/seed_db.py
```