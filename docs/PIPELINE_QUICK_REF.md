# Log Processing Pipeline - Quick Reference

**Last Updated**: November 17, 2025

## Overview

The Log Processing Pipeline provides a complete workflow for importing and validating contest logs. It combines Cabrillo parsing, database storage, and comprehensive validation in a single streamlined process.

---

## Quick Start

### Process a Single File

```python
from src.services.log_processing_pipeline import process_cabrillo_files

# Import and validate
result = process_cabrillo_files("log.txt", validate=True)

print(result['message'])
# Output: Successfully processed AA2A: 718 QSOs (711 valid, 6 duplicates, 1 invalid)
```

### Process a Directory

```python
result = process_cabrillo_files("logs_sa10m_2025/", validate=True)

print(f"Files: {result['successful']}/{result['total_files']}")
print(f"QSOs: {result['total_contacts']} ({result['valid_contacts']} valid)")
```

### Using the Demo Script

```bash
# Single file
python demo_pipeline.py logs/AA2A.txt

# Directory
python demo_pipeline.py logs_sa10m_2025/

# Custom database
python demo_pipeline.py logs/ my_contest.db
```

---

## Pipeline Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    LOG PROCESSING PIPELINE                   │
└─────────────────────────────────────────────────────────────┘

1. IMPORT PHASE
   ├─ Parse Cabrillo file
   ├─ Extract header and QSO data
   ├─ Create/find contest in database
   ├─ Create log entry
   └─ Import ALL contacts (including duplicates)

2. VALIDATION PHASE
   ├─ Load contest rules
   ├─ Sort contacts by timestamp
   ├─ Duplicate detection
   ├─ Exchange validation (RS/RST, CQ zone)
   ├─ Callsign validation
   ├─ Time validation (contest period)
   ├─ Band/mode validation
   └─ Update database with results

3. RESULTS
   └─ Return comprehensive statistics
```

---

## API Reference

### LogProcessingPipeline Class

```python
from src.services.log_processing_pipeline import LogProcessingPipeline
from src.database.db_manager import DatabaseManager

db = DatabaseManager("contest.db")
pipeline = LogProcessingPipeline(db, rules_file=None)
```

**Methods:**

#### process_file()
```python
result = pipeline.process_file(
    file_path="log.txt",
    contest_id=None,  # Auto-detect from log
    validate=True     # Run validation after import
)
```

**Returns:**
```python
{
    'success': True,
    'file': 'log.txt',
    'import': {...},      # Import results
    'validation': {...},  # Validation results
    'message': 'Successfully processed AA2A: 718 QSOs...'
}
```

#### process_directory()
```python
results = pipeline.process_directory(
    directory_path="logs/",
    pattern="*.txt",
    contest_id=None,
    validate=True
)
```

**Returns:**
```python
{
    'total_files': 916,
    'successful': 850,
    'failed': 66,
    'total_contacts': 45123,
    'valid_contacts': 44892,
    'duplicate_contacts': 189,
    'invalid_contacts': 42,
    'details': [...],  # Individual file results
    'message': 'Processed 850/916 files successfully...'
}
```

#### validate_existing_logs()
```python
# Re-validate logs already in database
results = pipeline.validate_existing_logs(log_ids=None)
```

---

## Validation Rules

### Duplicate Detection

**Rule**: Same callsign + same band + same mode

```python
# First contact: OK
QSO: 28500 PH 2025-03-08 1200 TEST 59 13 W1AW 59 05  ✓

# Same station, same band, same mode: DUPLICATE
QSO: 28500 PH 2025-03-08 1300 TEST 59 13 W1AW 59 05  ✗ DUPLICATE

# Same station, different mode: OK
QSO: 28025 CW 2025-03-08 1400 TEST 599 13 W1AW 599 05  ✓
```

### Exchange Validation

**RS/RST Format:**
- SSB/PH: 2 digits (e.g., "59")
- CW: 3 digits (e.g., "599")

**CQ Zone:**
- Must be number 1-40

**Examples:**
```
✓ Valid:   59 13  (SSB)
✓ Valid:   599 25 (CW)
✗ Invalid: 5 13   (missing digit)
✗ Invalid: 59 45  (zone > 40)
✗ Invalid: 599 D  (not a number)
```

### Callsign Validation

**Basic Format:**
- Must have letters and numbers
- Only A-Z, 0-9, and / allowed

**Examples:**
```
✓ Valid:   W1AW, K1ABC, LU1ABC
✓ Valid:   G4OPE/P, W1AW/MM
✗ Invalid: 123, ABC, W1AW!
```

### Time Validation

**Rule**: QSO must be within contest period

```python
Contest: 2025-03-08 00:00 to 2025-03-09 23:59:59

✓ 2025-03-08 12:00  (OK)
✗ 2025-03-07 23:00  (before contest)
✗ 2025-03-10 01:00  (after contest)
```

---

## Result Structures

### Import Result

```python
{
    'success': True,
    'log_id': 1,
    'callsign': 'AA2A',
    'qso_count': 718,
    'contest_id': 3,
    'contest_name': 'SA10-DX',
    'parse_errors': [],
    'parse_warnings': [],
    'message': 'Successfully imported 718 QSOs for AA2A'
}
```

### Validation Result

```python
{
    'total_contacts': 718,
    'valid_contacts': 711,
    'duplicate_contacts': 6,
    'invalid_contacts': 1,
    'errors': [
        'Duplicate contact (same callsign/band/mode)',
        'Invalid CQ zone format: "D" (must be a number 1-40)',
        ...
    ],
    'warnings': [
        'Mobile station: W1AW/MM',
        ...
    ]
}
```

---

## Database Updates

### Contact Fields Updated

After validation, the following fields are updated:

```python
contact.is_valid = True/False
contact.is_duplicate = True/False
contact.validation_status = 'valid' | 'duplicate' | 'invalid'
contact.validation_message = 'Error details...'
contact.points = 0  # For duplicates/invalid
```

### Query Validated Contacts

```python
from src.database.repositories import ContactRepository

with db.get_session() as session:
    repo = ContactRepository(session)
    
    # Get all contacts
    all_contacts = repo.get_all_for_log(log_id=1)
    
    # Get only valid contacts
    valid_contacts = repo.get_valid_for_log(log_id=1)
    
    # Get duplicates
    duplicates = [c for c in all_contacts if c.is_duplicate]
```

---

## Error Handling

### Common Errors

**1. File Not Found**
```python
{
    'success': False,
    'message': 'File not found: log.txt'
}
```

**2. Parse Errors**
```python
{
    'success': False,
    'message': 'Parse errors: Missing CALLSIGN tag; Invalid QSO format'
}
```

**3. Database Errors**
```python
{
    'success': False,
    'message': 'Error importing log: UNIQUE constraint failed'
}
```

### Handling Errors

```python
result = pipeline.process_file("log.txt")

if not result['success']:
    print(f"Error: {result['message']}")
    
    if result['import']:
        print(f"Parse errors: {result['import']['parse_errors']}")
        print(f"Parse warnings: {result['import']['parse_warnings']}")
```

---

## Configuration

### Custom Rules File

```python
pipeline = LogProcessingPipeline(
    db_manager,
    rules_file="config/contests/my_contest.yaml"
)
```

### Skip Validation

```python
# Import only, no validation
result = pipeline.process_file("log.txt", validate=False)
```

### Custom Database

```python
db = DatabaseManager("my_contest.db")
pipeline = LogProcessingPipeline(db)
```

---

## Performance Tips

### Batch Processing

For large directories, use batch processing:

```python
# Process all files at once
results = pipeline.process_directory("logs/")

# Much faster than processing individually
```

### Database Optimization

```python
# Let pipeline create tables automatically
pipeline = LogProcessingPipeline(db)  # Creates tables if needed

# Or pre-create for faster processing
db.create_all_tables()
pipeline = LogProcessingPipeline(db)
```

### Memory Management

For very large directories (1000+ files), consider processing in chunks:

```python
import glob
from pathlib import Path

files = list(Path("logs/").glob("*.txt"))

# Process in chunks of 100
for i in range(0, len(files), 100):
    chunk = files[i:i+100]
    for file in chunk:
        result = pipeline.process_file(str(file))
        # Process result
```

---

## Examples

### Example 1: Import All Logs, Then Validate

```python
# Step 1: Import all logs (fast)
for file in log_files:
    pipeline.process_file(file, validate=False)

# Step 2: Validate all logs in batch
pipeline.validate_existing_logs()
```

### Example 2: Find All Duplicates

```python
from src.database.repositories import ContactRepository

with db.get_session() as session:
    repo = ContactRepository(session)
    contacts = repo.get_all_for_log(log_id=1)
    
    duplicates = [c for c in contacts if c.is_duplicate]
    
    for dup in duplicates:
        print(f"{dup.qso_datetime} - {dup.call_received} "
              f"({dup.band} {dup.mode})")
```

### Example 3: Generate Validation Report

```python
result = pipeline.process_file("log.txt")

if result['validation']:
    val = result['validation']
    
    print(f"Validation Report for {result['import']['callsign']}")
    print(f"=" * 60)
    print(f"Total QSOs:     {val['total_contacts']}")
    print(f"Valid:          {val['valid_contacts']}")
    print(f"Duplicates:     {val['duplicate_contacts']}")
    print(f"Invalid:        {val['invalid_contacts']}")
    print()
    
    if val['errors']:
        print("Errors:")
        for error in val['errors']:
            print(f"  - {error}")
```

---

## Troubleshooting

### Problem: "No such table: contests"

**Solution**: Database tables not created

```python
db = DatabaseManager("contest.db")
db.create_all_tables()  # Create tables
pipeline = LogProcessingPipeline(db)
```

### Problem: Duplicates not being marked

**Check**:
1. Validation is enabled: `validate=True`
2. Database was updated: Check `contact.is_duplicate`
3. Contest dates are correct

### Problem: All QSOs marked invalid

**Check**:
1. Contest dates in database
2. QSO timestamps are within contest period
3. Contest start/end dates are correct

---

## See Also

- **Phase 4.1 Completion**: `docs/PHASE_4_1_COMPLETION.md`
- **Duplicate Handling**: `DUPLICATE_IMPORT_VERIFIED.md`
- **Database Schema**: `docs/DATABASE_SCHEMA.md`
- **Cabrillo Parser**: `docs/CABRILLO_PARSER_QUICK_REF.md`
- **Implementation Plan**: `IMPLEMENTATION_PLAN.md`

---

**Document Version**: 1.0  
**Created**: November 17, 2025  
**Status**: Phase 4.1 Complete

