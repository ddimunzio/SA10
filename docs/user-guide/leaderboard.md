# Leaderboard Tab

The **Leaderboard** tab displays the final ranked results for the active contest with filtering, sorting, and export options.

---

## Leaderboard Table

| Column | Description |
|--------|-------------|
| **#** | Rank (position in current sort order) |
| **Callsign** | Station callsign |
| **Category** | Combined operator / mode / power category |
| **Final Score** | Total contest score (points × multipliers) |
| **Total QSOs** | All contacts submitted |
| **Valid QSOs** | Contacts that survived cross-check |
| **Dupes** | Duplicate contacts removed |
| **Points** | Raw QSO point total |
| **Multipliers** | Total multiplier count (WPX + CQ zones) |

Click any **column header** to sort by that column. Click again to reverse the order.

---

## Filters

### Callsign filter

Type part of a callsign in the **Filter callsign** box. The table updates in real time as you type, showing only rows where the callsign contains the entered text.

### Category filter

The **Category** dropdown is populated automatically from the categories present in the current contest. Select a category to show only those entries, or choose **All** to show everyone.

### Area filter

| Option | Shows |
|--------|-------|
| **World** | All stations (default) |
| **Argentina** | Stations with LU, LW, LO, LP, LQ, AY, AZ prefixes |
| **South America** | All SA stations (including Argentina) |
| **DX** | Non-South-American stations |

---

## Actions

### ↻ Refresh Leaderboard

Reloads scores from the database. Use this after running the scorer to see updated results.

### ⬇ Export to Excel

Exports the full leaderboard (all rows, before any filter) to an Excel `.xlsx` file. A save dialog lets you choose the location.

The workbook contains one sheet with all columns plus calculated rank.

### ⬇ Export Scores CSV

Exports a lightweight CSV with callsign and key score columns. Useful for sharing or further analysis in spreadsheet tools.

### ⬇ QSO Report (Excel)

Exports a detailed per-QSO workbook with one row per contact across all logs. Columns include callsign, band, mode, frequency, timestamp, RST sent/received, exchange values, QSO points, and cross-check status.

!!! tip "Export tip"
    All exports use the **full unfiltered dataset** regardless of the active callsign / category / area filter.
