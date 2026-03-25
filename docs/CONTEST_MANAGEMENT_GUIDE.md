# Contest Management Guide

## Overview

The SA10 contest scoring system requires explicit contest creation before importing logs. This design ensures:
- **One contest at a time**: Focus on scoring a single contest
- **No auto-population**: Explicit control over contest data
- **Clean separation**: Contest metadata managed separately from logs

## Workflow

### 1. Create a Contest

Before importing any logs, create the contest:

```bash
python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"
```

Parameters:
- **name**: Full contest name (e.g., "SA10M 2025")
- **slug**: Unique identifier (e.g., "sa10m-2025")
- **start_date**: Contest start date and time (YYYY-MM-DD HH:MM)
- **end_date**: Contest end date and time (YYYY-MM-DD HH:MM)
- **--rules**: (Optional) Path to custom rules YAML file

The command will output the contest ID, which you'll need for importing logs.

### 2. Import Logs

Import logs with the contest ID:

```bash
# Import entire directory
python import_logs.py --contest-id 1 --clean logs_sa10m_2025/

# Import single file
python import_logs.py --contest-id 1 path/to/log.cbr
```

### 3. Automated Import

Use the all-in-one script that creates the contest and imports logs:

```bash
python import_all.py
```

This script:
1. Cleans the database
2. Creates the SA10M 2025 contest
3. Imports all logs from `logs_sa10m_2025/` directory

## Contest Management Commands

### List All Contests

```bash
python manage_contest.py list
```

Output:
```
ID    Name                           Slug                 Start Date          
================================================================================
1     SA10M 2025                     sa10m-2025           2025-03-08 00:00    

Total: 1 contest(s)
```

### Show Contest Details

```bash
python manage_contest.py show 1
```

Output:
```
======================================================================
Contest Details (ID: 1)
======================================================================
Name:       SA10M 2025
Slug:       sa10m-2025
Start Date: 2025-03-08 00:00:00
End Date:   2025-03-09 23:59:59
Rules File: config/contests/sa10m.yaml
Created:    2025-11-19 10:30:45
Updated:    2025-11-19 10:30:45

Logs Submitted: 150

Callsigns:
  - K1ABC
  - W2DEF
  ...
```

### Delete a Contest

⚠️ **Warning**: This deletes the contest and ALL associated logs and contacts!

```bash
python manage_contest.py delete 1
```

You'll be prompted to confirm:
```
WARNING: You are about to delete:
  Contest: SA10M 2025 (ID: 1)
  This will also delete 150 log(s) and all their contacts!

Type 'yes' to confirm: 
```

## Database Schema

The contests table stores:
- **id**: Unique contest identifier (auto-increment)
- **name**: Full contest name
- **slug**: Unique URL-friendly identifier
- **start_date**: Contest start timestamp
- **end_date**: Contest end timestamp
- **rules_file**: Path to contest rules YAML
- **created_at**: Record creation timestamp
- **updated_at**: Last update timestamp

## Design Rationale

### Why Manual Contest Creation?

1. **Explicit Control**: You decide when and how contests are created
2. **Data Integrity**: Prevents accidental creation of duplicate contests
3. **Simplified Workflow**: One contest at a time, focused scoring
4. **Clear Separation**: Contest metadata managed independently

### Why Contest ID Required?

- **No Ambiguity**: Logs are always associated with the correct contest
- **Batch Operations**: Import multiple logs to the same contest efficiently
- **Validation**: Contest dates used to validate QSO timestamps

## Examples

### Scenario 1: First Time Setup

```bash
# Step 1: Create contest
python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"
# Output: Contest created successfully! ID: 1

# Step 2: Import logs
python import_logs.py --contest-id 1 --clean logs_sa10m_2025/
```

### Scenario 2: Import Additional Logs

```bash
# Contest already exists (ID: 1)
python import_logs.py --contest-id 1 new_logs/CE2ABC_SSB.txt
```

### Scenario 3: Re-import from Scratch

```bash
# Delete existing contest
python manage_contest.py delete 1

# Create new contest
python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"

# Import all logs
python import_logs.py --contest-id 1 --clean logs_sa10m_2025/
```

### Scenario 4: Multiple Contests (Future)

```bash
# Create first contest
python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"
# ID: 1

# Import logs for first contest
python import_logs.py --contest-id 1 logs_sa10m_2025/

# Create second contest
python manage_contest.py create "SA10M 2026" sa10m-2026 "2026-03-14 00:00" "2026-03-15 23:59"
# ID: 2

# Import logs for second contest
python import_logs.py --contest-id 2 logs_sa10m_2026/
```

## Tips

- **Always note the contest ID** when creating a contest
- **Use descriptive slugs** with year for easy identification
- **Check existing contests** with `list` before creating new ones
- **Backup your database** before deleting contests
- **Use import_all.py** for quick start with SA10M 2025

## Troubleshooting

### "Contest ID X not found"
- Run `python manage_contest.py list` to see available contests
- Create the contest if it doesn't exist

### "Contest with slug 'xxx' already exists"
- Use a different slug or delete the existing contest
- Check with `python manage_contest.py list`

### Import fails with validation errors
- Verify contest dates match the log QSO dates
- Check if logs are in correct Cabrillo format

---

**See Also:**
- `IMPORT_QUICKSTART.md` - Quick start guide for importing logs
- `docs/DATABASE_SCHEMA.md` - Complete database documentation
- `docs/IMPORT_LOGS_GUIDE.md` - Detailed import guide

