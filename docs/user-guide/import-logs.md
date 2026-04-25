# Import Logs Tab

The **Import Logs** tab loads Cabrillo contest log files (`.cbr`, `.txt`) into the database for the active contest.

---

## Log Source

Choose how to provide the log files:

| Mode | Use when |
|------|----------|
| **Directory** | You have a folder containing many log files (typical for a full contest run) |
| **Single file** | You want to add or update one specific station's log |

Click **Browse…** to open a file-picker dialog, or type the path directly into the Path field.

!!! info "Supported file extensions"
    The directory import picks up `.txt`, `.log`, and `.cbr` files. Other file types in the folder are ignored.

---

## Options

### Contest ID

Automatically populated from the **active contest** set in the Contests tab. You can also type a contest ID manually if you need to import into a different contest without switching the active one.

### Clear ALL contest data before import

When checked, all logs, contacts, and scores belonging to the active contest are **deleted** before the new files are processed. Use this for a clean re-import from scratch.

!!! warning "Clear option is destructive"
    Clearing the contest data is irreversible within the current session. Only enable this when you intentionally want to start fresh.

---

## Running the Import

Click **▶ Import Logs** to start. The operation runs in a background thread so the UI stays responsive.

### What happens during import

1. Each Cabrillo file is parsed (header metadata + QSO lines)
2. The station callsign is extracted from the `CALLSIGN:` header
3. If a log for the same callsign already exists in the contest, it is **replaced** (most-recent submission wins)
4. All contacts are stored with their band, mode, frequency, RST, and exchange fields
5. A summary is printed in the Output Log:

```
Import done — 666 accepted file(s): 604 new, 62 replacement(s), 3 skipped/failed.
Contest now has 601 station log(s) for scoring.
```

### Replacement logic

If a station re-submits their log, the new file **replaces** the previous one. The count of unique station logs can therefore be lower than the number of accepted files.

### Skipped / failed files

A file is skipped when:
- It cannot be parsed as a valid Cabrillo file
- The `CALLSIGN:` field is missing or malformed
- A database error occurs during insert

Errors are shown in yellow in the Output Log with the filename and reason.

---

## After Import

The Contest list in the **Contests** tab updates automatically to reflect the new log count. Proceed to the **Cross-Check** tab.
