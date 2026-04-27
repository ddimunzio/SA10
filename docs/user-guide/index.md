# User Guide — Desktop Application

The SA10M Contest Manager is a desktop application built with Python/Tkinter. It provides a tabbed interface that takes you through the complete contest scoring workflow.

---

## Application Layout

![SA10M Contest Manager — main window](../assets/images/app-overview.png)


### File Menu
- **New Database…** — create a blank database file, initialise all tables, and automatically import DXCC country data (see [Creating a New Database](#creating-a-new-database))
- **Open Database…** — open an existing database file
- **Update DXCC Data…** — import or refresh the CTY country/prefix data into the active database (required before scoring; runs automatically on new databases)

### Header Bar
- Shows the **active database file** path on the right side
- **Change** button opens a file browser to switch to an existing database

### Output Log
- A scrolling console at the bottom captures all operation output
- Color-coded: white = normal, yellow = warnings, green = success, red = errors
- **Clear Log** removes all messages

### Status Bar
- Shows the current operation state (Ready / Importing logs… / Scoring logs…)
- Animated progress bar while a background task is running

---

## Recommended Workflow

Follow the tabs in order for a clean contest run:

```
1. Contests  →  2. Import Logs  →  3. Cross-Check  →  4. Scoring  →  5. Leaderboard
```

| Step | Tab / Action | What happens |
|------|-------------|-------------|
| 0 | **File → Update DXCC Data…** | Load country/prefix data — required before scoring (automatic on new databases) |
| 1 | [Contests](contests.md) | Create the contest record and set it as active |
| 2 | [Import Logs](import-logs.md) | Load Cabrillo log files from a folder |
| 3 | [Cross-Check](cross-check.md) | Validate contacts across all logs (NIL / busted) |
| 4 | [Scoring](scoring.md) | Calculate points and multipliers |
| 5 | [Leaderboard](leaderboard.md) | Browse results, export to Excel or CSV |

---

---

## Creating a New Database

Every contest season (or whenever you want a clean slate) you can create a new, empty database directly from the application — no command-line tools required.

1. Open the **File** menu → **New Database…**
2. Choose a location and filename (e.g. `sa10m_2026.db`) and click **Save**.
3. If the file already exists you will be asked to confirm the overwrite.
4. The database is created, all tables are initialised, and **DXCC country data is imported automatically** from the bundled `cty_wt.dat` file.
5. The header bar updates to show the new database path and the Contests tab reloads (empty).

You can now proceed to create a contest record and start importing logs.

!!! tip "Keep one database per year"
    Using a separate database for each contest edition (e.g. `sa10m_2025.db`, `sa10m_2026.db`) keeps data isolated and makes archiving straightforward. Use **Open Database…** to switch between them at any time.

!!! warning "Opening an older database"
    Databases created before version 2026-04 may not have DXCC data loaded. If scores seem incorrect (all zeros), use **File → Update DXCC Data…** to populate the country table, then re-run scoring.

---

## Launching the Application

```bash
# Activate the virtual environment first
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / Mac

# Launch
python app_ui.py
```
