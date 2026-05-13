# Getting Started

This guide is for the current SA10M Contest Manager application as it exists in this repository today. The normal entry point is the desktop UI in `app_ui.py`; the helper scripts are still available for batch or maintenance work.

## Prerequisites

- Python 3.10 or newer
- pip
- PowerShell on Windows, or a shell that can activate the virtual environment

## Install and Launch

```powershell
# From the repository root
cd C:\Users\lw5hr\proyects\SA10

# Create the virtual environment if needed
python -m venv .venv

# Activate it
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Launch the desktop application
python app_ui.py
```

If you only want to sanity-check the environment without opening the GUI, run:

```powershell
python manage_contest.py list
```

## First Run Workflow

1. Open `File -> New Database...` and create a database for the contest season.
2. Let the application initialise tables and import bundled DXCC data.
3. Go to the `Contests` tab and create or select the active contest.
4. Import Cabrillo logs from the `Import Logs` tab.
5. Run `Cross-Check` to populate NIL, busted-call, and unique-call results.
6. Run `Scoring` to compute final scores and multiplier totals.
7. Review `Leaderboard` and `Statistics`, then export Excel or CSV reports if needed.

## Recommended Test Commands

```powershell
# Full suite
pytest

# Core scoring and rules
pytest tests/test_rules_engine.py tests/test_sa10m_scoring.py -v

# Import and cross-check slice
pytest tests/test_log_import.py tests/test_cross_check_rules.py -v
```

## Main Repository Layout

```text
SA10/
|-- app_ui.py
|-- manage_contest.py
|-- import_logs.py
|-- run_cross_check.py
|-- update_dxcc_data.py
|-- config/
|   `-- contests/
|-- docs/
|   |-- user-guide/
|   `-- es/
|-- src/
|   |-- core/
|   |-- database/
|   |-- parsers/
|   `-- services/
`-- tests/
```

## Useful Commands

```powershell
# List contests
python manage_contest.py list

# Create a contest
python manage_contest.py create "SA10M 2026" sa10m-2026 "2026-03-14 00:00" "2026-03-15 23:59"

# Import a folder of logs
python import_logs.py --contest-id 1 logs_sa10m__2026

# Run cross-check from the CLI
python run_cross_check.py --contest-id 1
```

## Notes

- `main.py` is still present but it is not the primary application entry point.
- New databases automatically load DXCC data from the bundled `cty_wt.dat` file.
- The documentation site under `docs/` includes both English and Spanish content.

## Next Reading

- `docs/user-guide/index.md` for the GUI workflow
- `docs/IMPORT_LOGS_GUIDE.md` for batch import details
- `docs/DXCC_DATA_GUIDE.md` for country/prefix data maintenance
- `docs/es/PRIMEROS_PASOS.md` for the Spanish version of this guide

