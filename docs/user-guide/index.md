# User Guide — Desktop Application

The SA10M Contest Manager is a desktop application built with Python/Tkinter. It provides a tabbed interface that takes you through the complete contest scoring workflow.

---

## Application Layout

```
┌─────────────────────────────────────────────────────────────┐
│  SA10M Contest Manager          DB: sa10_contest.db [Change] │
├─────────────────────────────────────────────────────────────┤
│  Contests │ Import Logs │ Cross-Check │ Scoring │ Leaderboard│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   (active tab content)                                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Output Log                                   [Clear Log]   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [00:00:00] Ready...                                  │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Ready                                    [progress bar]    │
└─────────────────────────────────────────────────────────────┘
```

### Header Bar
- Shows the **active database file** path on the right side
- **Change** button opens a file browser to switch databases

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

| Step | Tab | What happens |
|------|-----|-------------|
| 1 | [Contests](contests.md) | Create the contest record and set it as active |
| 2 | [Import Logs](import-logs.md) | Load Cabrillo log files from a folder |
| 3 | [Cross-Check](cross-check.md) | Validate contacts across all logs (NIL / busted) |
| 4 | [Scoring](scoring.md) | Calculate points and multipliers |
| 5 | [Leaderboard](leaderboard.md) | Browse results, export to Excel or CSV |

---

## Launching the Application

```bash
# Activate the virtual environment first
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / Mac

# Launch
python app_ui.py
```
