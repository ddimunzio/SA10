# Database Quick Reference

## Initialize Database

```python
from src.database.db_manager import init_database, populate_reference_data

# Create database with tables
db = init_database("sqlite:///sa10_contest.db")

# Add reference data (provinces, DXCC)
with db.get_session() as session:
    populate_reference_data(session)
```

## Common Queries

### Get all logs for a contest
```python
from src.database.models import Log

with db.get_session() as session:
    logs = session.query(Log).filter_by(contest_id=1).all()
```

### Get contacts for a log
```python
from src.database.models import Contact

with db.get_session() as session:
    contacts = session.query(Contact).filter_by(log_id=1).all()
```

### Get valid contacts only
```python
contacts = session.query(Contact)\
    .filter_by(log_id=1, is_valid=True)\
    .all()
```

### Get contacts by band and mode
```python
contacts = session.query(Contact)\
    .filter_by(log_id=1, band="10m", mode="PH")\
    .all()
```

### Count duplicates
```python
duplicates = session.query(Contact)\
    .filter_by(log_id=1, is_duplicate=True)\
    .count()
```

### Get multipliers
```python
from src.database.models import CTYData

# Get all South American entities from CTY data
sa_entities = session.query(CTYData)\
    .filter_by(continent="SA")\
    .all()

# Lookup callsign prefix
def lookup_prefix(callsign):
    # Get all CTY entries and find matching prefix
    for entry in session.query(CTYData).all():
        for prefix in entry.prefixes:
            if callsign.startswith(prefix):
                return entry
    return None
```

## Pydantic Models Usage

### Validate a contact
```python
from src.core.models import ContactCreate

# This will validate automatically
contact_data = ContactCreate(
    log_id=1,
    frequency=28300,
    mode="PH",
    qso_date="2025-03-08",
    qso_time="1207",
    call_sent="LU1HLH",
    rst_sent="59",
    exchange_sent="13",
    call_received="DP7D",
    rst_received="59",
    exchange_received="14"
)

# Access computed fields
print(contact_data.qso_datetime)  # datetime object
print(contact_data.band)  # "10m"
```

## Database Schema Overview

```
contests
├── id (PK)
├── name
├── slug
├── start_date
├── end_date
└── rules_file

logs
├── id (PK)
├── contest_id (FK → contests.id)
├── callsign
├── category_* (9 fields)
├── operators, name, address, email
└── claimed_score

contacts
├── id (PK)
├── log_id (FK → logs.id)
├── frequency, mode, qso_datetime
├── call_sent, rst_sent, exchange_sent
├── call_received, rst_received, exchange_received
├── band (derived)
├── points, is_multiplier
├── is_valid, is_duplicate
└── matched_contact_id (FK → contacts.id)

scores
├── id (PK)
├── log_id (FK → logs.id, unique)
├── total_qsos, valid_qsos
├── total_points, multipliers
├── final_score
└── *_by_band, *_by_mode (JSON)
```

## CLI Commands

```bash
# Run test
python test_database.py

# Initialize from Python
python -c "from src.database.db_manager import init_database; db = init_database('sqlite:///contest.db')"
```

