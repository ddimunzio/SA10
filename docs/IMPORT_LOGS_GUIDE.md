# Log Import Guide

## Quick Start

### Import logs with clean database (recommended for fresh start)

```bash
python import_logs.py --clean logs_sa10m_2025/
```

This will:
1. **Delete all data** from the database
2. Recreate all tables
3. Import all `.txt` files from `logs_sa10m_2025/`
4. Validate all contacts
5. Show summary statistics

### Import without cleaning database

```bash
python import_logs.py logs_sa10m_2025/
```

This will add/update logs without deleting existing data.

### Import a single file

```bash
python import_logs.py --clean logs_sa10m_2025/CE1KR_SSB_4B4W.txt
```

### Import without validation (faster)

```bash
python import_logs.py --clean --no-validate logs_sa10m_2025/
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `path` | **(Required)** Path to Cabrillo file or directory |
| `--clean` | Clear database before importing |
| `--db PATH` | Database file path (default: `sa10_contest.db`) |
| `--rules PATH` | Custom contest rules YAML file |
| `--no-validate` | Skip validation after import |
| `--pattern PATTERN` | File pattern for directory import (default: `*.txt`) |
| `-v, --verbose` | Enable verbose logging |

## Examples

### Example 1: Fresh Import of All Logs

```bash
python import_logs.py --clean logs_sa10m_2025/
```

Output:
```
======================================================================
SA10M CONTEST LOG IMPORTER
======================================================================

🗑️  Cleaning database...
✓ Database cleaned

📂 Source: logs_sa10m_2025
💾 Database: sa10_contest.db
✓ Validation: enabled

Processing directory: logs_sa10m_2025
Pattern: *.txt
----------------------------------------------------------------------
Processing 100 files from logs_sa10m_2025
...

Batch Summary:
  Files processed: 98/100
  Total QSOs: 15234
  Valid: 14502
  Duplicates: 532
  Invalid: 200

======================================================================
✓ Import complete
======================================================================
```

### Example 2: Import Single Log

```bash
python import_logs.py --clean CE1KR_SSB_4B4W.txt
```

### Example 3: Import CW logs only

```bash
python import_logs.py --clean --pattern "*_CW_*.txt" logs_sa10m_2025/
```

### Example 4: Import to different database

```bash
python import_logs.py --clean --db test.db logs_sa10m_2025/
```

### Example 5: Fast import without validation

```bash
python import_logs.py --clean --no-validate logs_sa10m_2025/
```

Then validate later:
```python
from src.database.db_manager import DatabaseManager
from src.services.log_processing_pipeline import LogProcessingPipeline

db = DatabaseManager('sa10_contest.db')
pipeline = LogProcessingPipeline(db)
results = pipeline.validate_existing_logs()
print(results)
```

## Programmatic Usage

### Python API

```python
from src.database.db_manager import DatabaseManager
from src.services.log_processing_pipeline import LogProcessingPipeline

# Initialize
db_manager = DatabaseManager('sa10_contest.db')

# Clean database
db_manager.reset_database()

# Create pipeline
pipeline = LogProcessingPipeline(db_manager)

# Import single file
result = pipeline.process_file('logs_sa10m_2025/CE1KR_SSB_4B4W.txt')
print(result)

# Import directory
result = pipeline.process_directory('logs_sa10m_2025/')
print(result)

# Validate existing logs
result = pipeline.validate_existing_logs()
print(result)
```

### Simple one-liner

```python
from src.services.log_processing_pipeline import process_cabrillo_files

# This handles everything
result = process_cabrillo_files('logs_sa10m_2025/', db_path='sa10_contest.db')
```

## What Happens During Import?

### 1. Database Cleaning (if `--clean` is used)
- Drops all tables
- Recreates all tables (contests, logs, contacts, validation_results)

### 2. Log Import
For each Cabrillo file:
- Parse the Cabrillo format
- Extract log metadata (callsign, category, operators, etc.)
- Check if log already exists (by callsign)
- If log exists and new file is newer: **replace** log and contacts
- If log doesn't exist: **create** new log
- Import all QSOs/contacts (including duplicates)

### 3. Validation (if enabled)
For each log:
- Check for duplicate contacts (same call, band, mode, time)
- Validate callsign format
- Validate exchange format (RST, CQ Zone, serial number)
- Check if contact is within contest period
- Mark contacts as valid/invalid in database

### 4. Report Generation
- Summary statistics
- Error list (if any)

## Database Tables

After import, data is stored in:

- **contests**: Contest definitions (SA10M 2025, etc.)
- **logs**: Station logs (one per callsign)
- **contacts**: Individual QSOs
- **validation_results**: Validation status for each contact

## Troubleshooting

### Error: "AttributeError: 'DatabaseManager' object has no attribute 'initialize_database'"

The method name was changed. Use:
```python
db_manager.create_all_tables()  # Instead of initialize_database()
```

Or better, use the `import_logs.py` script which handles this automatically.

### Error: "UNIQUE constraint failed"

This happens if you import the same log twice. Solutions:
- Use `--clean` to start fresh
- The system now auto-replaces logs if file is newer
- Delete specific log from database first

### No validation results

Make sure you're not using `--no-validate` flag.

### Slow import

- Use `--no-validate` for faster import
- Run validation separately later

## Next Steps

After importing:

1. **Query the database** to verify data:
   ```python
   from src.database.db_manager import DatabaseManager
   from src.database.repositories import LogRepository, ContactRepository
   
   db = DatabaseManager('sa10_contest.db')
   with db.get_session() as session:
       log_repo = LogRepository(session)
       logs = log_repo.get_all()
       print(f"Total logs: {len(logs)}")
       for log in logs[:5]:
           print(f"  {log.callsign}: {log.qso_count} QSOs")
   ```

2. **Calculate scores** (Phase 4 - upcoming)

3. **Generate reports** (Phase 5 - upcoming)

## See Also

- [Database Schema](DATABASE_SCHEMA.md)
- [Cabrillo Parser Reference](CABRILLO_PARSER_QUICK_REF.md)
- [Rules Engine Reference](RULES_ENGINE_QUICK_REF.md)

