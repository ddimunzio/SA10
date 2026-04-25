# SA10M Contest Manager

**A complete scoring and management system for the SA10M Ham Radio Contest.**

SA10M is a 10-meter single-band amateur radio contest with stations from South America and around the world. This application handles the full contest workflow — from importing Cabrillo log files to cross-checking contacts and generating the final leaderboard.

---

## Key Features

- **Parse contest logs** — Cabrillo format (`.cbr`, `.txt`) with automatic duplicate detection
- **Configurable scoring engine** — YAML-based rules for QSO points and multipliers (WPX prefixes + CQ zones)
- **Cross-check pipeline** — validates contacts against all other submitted logs, flagging NIL and busted calls
- **UBN reports** — generates per-station Unique/Busted/Not-in-log reports
- **Leaderboard with filters** — sort and filter by category, operator area, callsign
- **Excel / CSV exports** — full QSO report and scores spreadsheet
- **Desktop GUI** — simple Tkinter interface, no server required

---

## Quick Navigation

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Getting Started**

    ---

    Install dependencies and run your first import in minutes.

    [:octicons-arrow-right-24: Getting Started](GETTING_STARTED.md)

-   :material-monitor:{ .lg .middle } **User Guide (UI)**

    ---

    Step-by-step guide to every tab of the desktop application.

    [:octicons-arrow-right-24: User Guide](user-guide/index.md)

-   :material-trophy:{ .lg .middle } **Contest Rules**

    ---

    SA10M scoring rules, multipliers, and exchange format.

    [:octicons-arrow-right-24: SA10M Quick Reference](SA10M_QUICK_REFERENCE.md)

-   :material-book-open-variant:{ .lg .middle } **Technical Reference**

    ---

    Database schema, log import pipeline, and service architecture.

    [:octicons-arrow-right-24: Technical Docs](DATABASE_SCHEMA.md)

</div>

---

## Typical Workflow

```mermaid
graph LR
    A[Create Contest] --> B[Import Logs]
    B --> C[Run Cross-Check]
    C --> D[Score All Logs]
    D --> E[View Leaderboard]
    E --> F[Export Results]
```

1. **Create a contest** — define name, slug, and date range in the Contests tab
2. **Import logs** — point to a folder of Cabrillo files; duplicates are handled automatically
3. **Cross-check** — compare every contact against all other logs to find NIL/busted entries
4. **Score** — calculate QSO points, WPX prefixes, and CQ zone multipliers
5. **Leaderboard** — browse results filtered by category or area, export to Excel

---

## Project Status

The system is fully operational for the **SA10M 2026** contest season with **601 station logs** processed and scored.

| Phase | Status |
|-------|--------|
| Foundation & Core Models | ✅ Complete |
| Rules Engine | ✅ Complete |
| Log Parsing (Cabrillo) | ✅ Complete |
| Cross-Check Pipeline | ✅ Complete |
| Scoring Engine | ✅ Complete |
| Desktop GUI | ✅ Complete |
