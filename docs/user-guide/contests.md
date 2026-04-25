# Contests Tab

The **Contests** tab is where you create and manage contest records. Every import and scoring run is tied to a specific contest, so this is always the first step.

---

## Create New Contest

Fill in the four fields and click **Create Contest**:

| Field | Example | Description |
|-------|---------|-------------|
| **Name** | `SA10M 2026` | Human-readable contest name |
| **Slug** | `sa10m-2026` | Unique identifier used internally and by the rules engine |
| **Start (YYYY-MM-DD HH:MM)** | `2026-03-14 00:00` | Contest start time in UTC |
| **End (YYYY-MM-DD HH:MM)** | `2026-03-15 23:59` | Contest end time in UTC |

!!! tip "Slug convention"
    Use lowercase letters, digits, and hyphens only. The slug must match a rules YAML file in `config/contests/`. For the standard SA10M contest use `sa10m`.

After clicking **Create Contest** the new record appears in the table below and a confirmation message is printed in the Output Log.

---

## Contest List

The table shows all contests stored in the current database:

| Column | Description |
|--------|-------------|
| **ID** | Auto-assigned numeric identifier |
| **Name** | Contest name |
| **Slug** | Internal identifier |
| **Start / End** | Contest period |
| **Logs** | Number of station logs imported for this contest |

### Buttons

- **↻ Refresh** — reload the list from the database (useful after external changes)
- **Select Active** — mark the highlighted contest as the *active contest*; this propagates to the Import Logs and Scoring tabs automatically
- **Delete** — permanently remove the selected contest and all its logs and scores

!!! warning "Delete is permanent"
    Deleting a contest removes all associated logs, contacts, and scores from the database. This cannot be undone.

---

## Active Contest

The **active contest** is displayed in bold on the right side of the button row. Once set, every other tab (Import Logs, Cross-Check, Scoring, Leaderboard) automatically targets this contest — you don't need to re-enter the contest ID anywhere.

To change the active contest, click a different row in the table and press **Select Active**.
