# Ham Radio Contest Manager

Configurable desktop scoring and contest-management software for amateur radio events.

The repository currently ships with the SA10M ruleset and supports the full workflow used for the 2026 season: contest creation, Cabrillo log import, cross-check validation, scoring, leaderboard review, statistics, and Excel/CSV exports.

## Current Status

The application is operational for the SA10M 2026 dataset.

- 666 source files processed
- 3 parse failures
- 62 replacement submissions resolved
- 601 final station logs scored and shown in the leaderboard

## Features

- Tkinter desktop UI for contest operations with no server required
- YAML-driven contest rules in `config/contests/`
- Cabrillo import from single files or whole folders
- Duplicate handling and replacement submission tracking
- Cross-check pipeline with NIL, busted-call, and unique-call detection
- SA10M scoring with WPX prefix and CQ zone multipliers
- Leaderboard filters by callsign, category, and operator area
- Statistics view with country, prefix, zone, UBN, and continent summaries
- Excel and CSV exports, including QSO and UBN reports

## Quick Start

```powershell
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install application dependencies
pip install -r requirements.txt

# Launch the desktop application
python app_ui.py
```

For a first run, create a new database from `File -> New Database...`, then create or select a contest and proceed through import, cross-check, scoring, leaderboard, and statistics.

## Command-Line Utilities

The desktop app is the primary entry point, but the repository also includes focused CLI scripts:

```powershell
# List contests in the default database
python manage_contest.py list

# Create a contest
python manage_contest.py create "SA10M 2026" sa10m-2026 "2026-03-14 00:00" "2026-03-15 23:59"

# Import a folder of Cabrillo logs
python import_logs.py --contest-id 1 logs_sa10m__2026

# Run cross-check validation
python run_cross_check.py --contest-id 1
```

## Testing

```powershell
# Run the full test suite
pytest

# Run a focused slice
pytest tests/test_rules_engine.py tests/test_sa10m_scoring.py -v
```

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Documentation Home](docs/index.md)
- [English User Guide](docs/user-guide/index.md)
- [Guia en Espanol](docs/es/index.md)
- [SA10M Quick Reference](docs/SA10M_QUICK_REFERENCE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Import Logs Guide](docs/IMPORT_LOGS_GUIDE.md)
- [DXCC Data Guide](docs/DXCC_DATA_GUIDE.md)

## Project Layout

```text
SA10/
|-- app_ui.py
|-- manage_contest.py
|-- import_logs.py
|-- run_cross_check.py
|-- config/
|   `-- contests/
|-- docs/
|-- src/
`-- tests/
```

## Notes

- `main.py` remains a lightweight placeholder entry point; use `app_ui.py` for normal operation.
- DXCC data can be refreshed from the GUI with `File -> Update DXCC Data...`.
- Additional contests can be added by providing a new YAML rules file and contest record.

