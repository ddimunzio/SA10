# Statistics Tab

The **Statistics** tab gives you a compact summary of the active contest after import, cross-check, and scoring have been run.

---

## Actions

### Refresh Statistics

Reloads the summary cards and participant tables from the database for the active contest.

### Export UBN List (Excel)

Creates an Excel workbook containing every contact flagged as one of the following:

- Not in log
- Invalid callsign
- Unique call

The export includes the operator callsign, QSO date/time, band, mode, sent and received exchange values, UBN type, reason, country, and WPX prefix.

---

## Summary Cards

### General

- **Total Participating Countries** — distinct countries represented by submitted logs
- **Total UBNs** — total contacts flagged as NIL, busted calls, or unique calls

### CW

- **CQ Zones** — distinct received CQ zones seen on CW
- **Prefixes** — distinct WPX prefixes worked on CW
- **Countries** — distinct countries worked on CW
- **UBNs** — cross-check issues found on CW contacts

### SSB

- **CQ Zones** — distinct received CQ zones seen on phone modes
- **Prefixes** — distinct WPX prefixes worked on phone modes
- **Countries** — distinct countries worked on phone modes
- **UBNs** — cross-check issues found on phone contacts

Phone totals include `PH`, `SSB`, `USB`, `LSB`, and `FM` contacts.

---

## Participants by Continent

The lower table groups submitted logs by continent using the callsign lookup data stored in the active database. This helps confirm that operator geography looks reasonable before publishing results.

---

## When to Use It

- After **Import Logs** to confirm participation counts
- After **Cross-Check** to review UBN volume
- After **Scoring** to sanity-check multipliers and coverage by mode

If the cards show empty country totals or obviously wrong geography, refresh DXCC data from the File menu and run scoring again.