# UBN Report Format Specification

**UBN**: Unique / Busted / Not-in-log Report  
**Purpose**: Identify errors in contest log submissions through cross-log validation

## Scoring Penalties

| Error Type | Effect on QSO Points | Effect on Multipliers |
|---|---|---|
| **DUPLICATE** | 0 points (not penalised) | Not counted |
| **UNIQUE** | Full points (QSO kept) | Counted as normal mult |
| **BUSTED** (Incorrect Call) | QSO removed (0 points) | Mult lost if no other valid QSO covered it |
| **NIL** (Not-in-Log) | QSO removed **+ extra 1× penalty** | Mult lost if no other valid QSO covered it |

> **NIL penalty detail**: The QSO is first removed from the valid pool (losing its
> point value once), and then an additional penalty equal to the QSO's raw point
> value is subtracted — effectively a **2× deduction** from the final points total.

## Raw vs Final Statistics

The UBN summary shows two rows for QSOs, points, multipliers, and score:

```
   1201  Raw    QSO before checking (does not include duplicates)
    903  Final  QSO after  checking reductions

   4216  Raw    QSO points
   3084  Final  QSO points

    411  Raw    mults
    398  Final  mults

1732776  Raw    score
1229604  Final  score
```

**Raw** figures are computed from all non-duplicate contacts, regardless of
validation status.  
**Final** figures reflect only valid contacts after all cross-check reductions.

### How multipliers are computed

Multipliers (WPX prefixes and CQ zones) are computed independently for raw and
final using **Python set logic** over raw contact data, not the database
`is_multiplier` flag. This ensures lost multipliers are correctly reported:

- A multiplier is counted **raw** if any non-duplicate contact claimed it.  
- A multiplier is counted **final** only if at least one **valid** contact
  claimed it (`is_valid = 1`).  
- If an invalid QSO was the sole contact for a given prefix or zone in that
  mode, that multiplier disappears from the final count.

Both types use **per_band_mode** scope (matching SA10M rules):  
`key = (band, mode, type, value)` — e.g. `('10m', 'SSB', 'zone', '14')`.

## Unique Call Fraud Detection (MASTER.SCP + Corroboration)

To distinguish genuine casual operators from fabricated callsigns, the system
applies a two-layer check before crediting a Unique Call:

1. **MASTER.SCP lookup** — the callsign is checked against the Super Check
   Partial database (`config/master.scp`). If found, the station is a known
   active contester and the QSO keeps its UNIQUE status.
2. **Cross-log corroboration** — if not in SCP, the system checks whether at
   least **one other submitted log** also worked the same callsign. If so, the
   QSO keeps its UNIQUE status.

If the callsign **fails both checks** (not in SCP **and** not corroborated by
any other log), it is reclassified as **BUSTED** with no suggested correction
(`correct ?` in the UBN report), and the QSO is removed without penalty credit.

### MASTER.SCP management

The SCP database can be downloaded from the Cross-Check tab in the UI:

- **URL**: `https://www.supercheckpartial.com/MASTER.SCP`  
- **Local path**: `config/master.scp`  
- The UI shows the current file size (callsign count) and last-updated date.



### Per-Station Report Format

```
================================================================================
UBN REPORT FOR: K1ABC
Contest: SA10M Contest 2025
Category: Single Operator Mixed
================================================================================

SUMMARY STATISTICS:
  Total QSOs claimed:        234
  Valid QSOs confirmed:      218
  Duplicate QSOs:            3
  Invalid QSOs:              1
  
  UNIQUE calls:              8  (3.4%)
  BUSTED calls:              3  (1.3%)
  NOT-IN-LOG:                4  (1.7%)
  
  Error Rate:                6.4%
  Confirmed Rate:            93.6%

================================================================================
UNIQUE CALLS (not found in any other submitted log):
================================================================================

These calls appear only in your log. They may be:
- Stations that did not submit logs
- Incorrectly copied callsigns
- Non-existent callsigns

  Band  Mode  Date-Time (UTC)  Call       Exchange
  ----  ----  ---------------  ---------  -------------
  28MHz SSB   2025-03-08 1234  K9XYZ      59  05
  28MHz CW    2025-03-08 1456  LU9ZZZ     599 13
  28MHz SSB   2025-03-08 1823  W1ABC/MM   59  11
  ...

================================================================================
BUSTED CALLS (incorrectly copied callsign):
================================================================================

Your log shows a call that does not match any submitted log, but is very
similar to another call that did submit. The other station may have worked you.

  Band  Mode  Date-Time (UTC)  Logged As  Should Be   Exchange
  ----  ----  ---------------  ---------  ----------  -------------
  28MHz SSB   2025-03-08 1456  W1ZZZ      W1XXX (*)   59  05
  28MHz CW    2025-03-08 1634  K9JX       K9JY  (*)   599 04
  28MHz SSB   2025-03-08 2103  LU1AZ      LU1AB (*)   59  13

  (*) = Station submitted a log and has you in their log with correct call

================================================================================
NOT-IN-LOG (NIL) - Other station has no record of QSO:
================================================================================

These contacts appear in your log, but the other station's log does not show
this QSO. Possible reasons:
- Other station did not log the contact
- Time/band/mode mismatch (outside tolerance window)
- Other station logged you with a different callsign

  Band  Mode  Date-Time (UTC)  Call       Your Exchange  Their Exchange
  ----  ----  ---------------  ---------  -------------  --------------
  28MHz CW    2025-03-08 1834  LU5ABC     599 05         599 13 (*)
  28MHz SSB   2025-03-08 1945  EA5BH      59  05         59  14 (*)
  28MHz SSB   2025-03-08 2234  PY2AA      59  05         (NOT FOUND)

  (*) = Other station's log shows a contact near this time/band/mode
        but not within ±5 minute tolerance window

================================================================================
NOTES:
================================================================================

1. Time tolerance: ±5 minutes for matching QSOs
2. UNIQUE calls may be valid if station did not submit a log
3. BUSTED calls are high-confidence errors - check your original log
4. NIL contacts may be timing errors or other station's logging mistakes

Review these errors carefully. Contest organizers may:
- Deduct points for BUSTED calls
- Deduct points for NIL contacts
- Remove UNIQUE calls from scoring

================================================================================
```

## Aggregate Summary Report Format

```
================================================================================
SA10M CONTEST 2025 - UBN AGGREGATE SUMMARY
================================================================================

Total Logs Submitted: 844
Total QSOs Claimed:   82,028
Valid QSOs:           79,345 (96.7%)
Duplicate QSOs:       1,876  (2.3%)
Invalid QSOs:         148    (0.2%)

Cross-checking Summary:
  UNIQUE calls:       4,234  (5.2%)
  BUSTED calls:       892    (1.1%)
  NOT-IN-LOG:         1,567  (1.9%)
  
Average error rate:   8.2%
Median error rate:    5.1%

================================================================================
TOP 20 STATIONS BY ERROR RATE:
================================================================================

  Rank  Callsign    QSOs  Errors  Error%  UNQ  BST  NIL
  ----  ---------   ----  ------  ------  ---  ---  ---
  1     XX1XXX      145   42      29.0%   18   12   12
  2     YY2YYY      89    23      25.8%   8    9    6
  3     ZZ3ZZZ      234   58      24.8%   22   15   21
  ...

================================================================================
TOP 20 STATIONS BY QUALITY (Lowest Error Rate):
================================================================================

  Rank  Callsign    QSOs  Errors  Error%  UNQ  BST  NIL
  ----  ---------   ----  ------  ------  ---  ---  ---
  1     AA1AAA      456   2       0.4%    1    0    1
  2     BB2BBB      389   3       0.8%    2    0    1
  3     CC3CCC      523   5       1.0%    3    1    1
  ...

================================================================================
MOST COMMONLY BUSTED CALLS:
================================================================================

Frequently confused callsigns (likely difficult to copy):

  Correct Call  Logged As     Count  Similar To
  ------------  ------------  -----  ----------
  K9JY          K9JX, K9JZ    12     K9JX(8), K9JZ(4)
  W1XXX         W1ZZZ, W1YYY  9      W1ZZZ(5), W1YYY(4)
  LU1AB         LU1AZ, LU1AC  7      LU1AZ(4), LU1AC(3)
  ...

================================================================================
UNIQUE CALL ANALYSIS:
================================================================================

Calls that appear in multiple logs (likely valid):
  2,134 calls appear in 2-5 logs (probably didn't submit)

Calls that appear in only one log (possibly busted):
  2,100 calls appear in exactly 1 log (need review)

Most active non-submitting stations (by QSO count):
  1. K9ZZ      - worked by 23 stations (115 QSOs) - DID NOT SUBMIT
  2. W1ABC     - worked by 19 stations (89 QSOs)  - DID NOT SUBMIT
  3. LU5XYZ    - worked by 17 stations (76 QSOs)  - DID NOT SUBMIT
  ...

================================================================================
STATISTICS BY BAND/MODE:
================================================================================

  Band   Mode  QSOs    Valid%  Dup%   Err%   UNQ%  BST%  NIL%
  -----  ----  ------  ------  -----  -----  ----  ----  ----
  28MHz  CW    42,156  97.2%   2.1%   0.7%   4.8%  0.9%  1.6%
  28MHz  SSB   39,872  96.2%   2.5%   1.3%   5.6%  1.3%  2.2%

Error rates are higher on SSB (more difficult copying conditions)

================================================================================
RECOMMENDATIONS:
================================================================================

1. Stations with >15% error rate should review their logging practices
2. Consider operator training for busted call reduction
3. Encourage more stations to submit logs (reduces UNIQUE calls)
4. Common busted calls should be noted for future contests

================================================================================
```

## Data Models

### UBNEntry (Pydantic Model)

```python
class UBNType(str, Enum):
    UNIQUE = "unique"
    BUSTED = "busted"
    NOT_IN_LOG = "nil"

class UBNEntry(BaseModel):
    """Single UBN entry for a contact"""
    log_id: int
    contact_id: int
    callsign: str
    timestamp: datetime
    band: str
    mode: str
    ubn_type: UBNType
    
    # For BUSTED calls
    suggested_call: Optional[str] = None
    similarity_score: Optional[float] = None
    other_station_has_qso: bool = False
    
    # For NIL
    other_log_id: Optional[int] = None
    time_difference_minutes: Optional[float] = None
    
    # Exchange data
    rst_sent: str
    exchange_sent: str
    rst_received: str
    exchange_received: str

class UBNReport(BaseModel):
    """Complete UBN report for a station"""
    callsign: str
    log_id: int
    contest_name: str
    category: str
    
    # Statistics
    total_qsos: int
    valid_qsos: int
    duplicate_qsos: int
    invalid_qsos: int
    
    unique_count: int
    busted_count: int
    nil_count: int
    
    error_rate: float
    confirmed_rate: float
    
    # Entries
    unique_entries: List[UBNEntry]
    busted_entries: List[UBNEntry]
    nil_entries: List[UBNEntry]
    
    generated_at: datetime
```

## SQL Queries

### 1. UNIQUE Call Detection

```sql
-- Find calls that appear in only one log
SELECT 
    c.callsign,
    COUNT(DISTINCT c.log_id) as log_count,
    COUNT(*) as qso_count
FROM contacts c
WHERE c.is_valid = 1
GROUP BY c.callsign
HAVING log_count = 1;
```

### 2. NOT-IN-LOG Detection

```sql
-- Find contacts where reciprocal QSO is missing
SELECT 
    c1.id as contact_id,
    c1.log_id,
    l1.callsign as station_call,
    c1.callsign as worked_call,
    c1.timestamp,
    c1.band,
    c1.mode,
    c1.rst_sent,
    c1.exchange_sent,
    c1.rst_received,
    c1.exchange_received
FROM contacts c1
INNER JOIN logs l1 ON c1.log_id = l1.id
LEFT JOIN logs l2 ON l2.callsign = c1.callsign
LEFT JOIN contacts c2 ON 
    c2.log_id = l2.id
    AND c2.callsign = l1.callsign
    AND c2.band = c1.band
    AND c2.mode = c1.mode
    AND ABS(JULIANDAY(c2.timestamp) - JULIANDAY(c1.timestamp)) < 0.000694  -- 1 min
WHERE 
    c1.is_valid = 1
    AND l2.id IS NOT NULL  -- Other station submitted a log
    AND c2.id IS NULL;     -- But no matching QSO found
```

### 3. BUSTED Call Detection (Python + SQL)

Busted call detection uses a **two-stage pipeline**:

**Stage 1 — Coarse candidate generation** (mode-independent)  
Levenshtein edit distance 1–2 is used as a fast filter to build a candidate
list of submitted calls that could be the intended callsign.

**Stage 2 — Mode-aware re-ranking**  
Candidates are re-scored using a mode-aware similarity function before
being checked for a reciprocal QSO:

| Mode | Algorithm | Rationale |
|------|-----------|----------|
| `CW` | Morse-weighted edit distance | Characters with similar Morse sequences (E/I, T/N, D/B, U/V …) receive a lower substitution cost and rank higher |
| `PH` / `SSB` / `FM` | Jaro-Winkler | Rewards shared prefixes; well-suited to phonetic copying errors |
| Other | Plain Levenshtein ratio | Unchanged fallback |

**Guards against false positives**
- A station is never suggested as a busted-call correction for its own
  logged call (self-reference guard).
- The same suggested call cannot be assigned to two different worked calls
  in the same log within 10 minutes.

```python
# Simplified representation of the actual implementation

# Stage 1: coarse filter (edit distance 1-2)
for worked_call in non_submitted_calls:
    candidates = [
        (sub, Levenshtein.ratio(worked_call, sub))
        for sub in submitted_calls
        if 1 <= Levenshtein.distance(worked_call, sub) <= 2
        and Levenshtein.ratio(worked_call, sub) >= 0.65
    ]

# Stage 2: re-rank per contact with mode-aware similarity
mode_ranked = sorted(
    [(sug, callsign_similarity(worked_call, sug, row.mode))
     for sug, _ in candidates],
    key=lambda x: x[1], reverse=True
)

for suggested_call, similarity in mode_ranked:
    if suggested_call == row.log_callsign:   # self-reference guard
        continue
    if reciprocal_qso_exists(suggested_call, log_callsign, timestamp, ±5min):
        mark_as_busted(worked_call, suggested_call, similarity)
        break
    if edit_distance == 1 and zone_matches(suggested_call, logged_exchange):
        # Zone-match fallback when reciprocal not found
        mark_as_busted(worked_call, suggested_call, similarity)
        break
```

**Cross-check reset**  
Before each cross-check run, contacts previously marked `invalid_callsign`,
`not_in_log`, or `unique_call` are **reset to `valid`** so that a re-run
always starts from clean import-time data. This prevents a wrongly-busted
call from remaining `is_valid=0` across subsequent runs.

```python
# Executed automatically at the start of check_all_logs()
UPDATE contacts
SET validation_status = 'valid', validation_notes = NULL, is_valid = 1
WHERE log_id IN (SELECT id FROM logs WHERE contest_id = :contest_id)
  AND validation_status IN ('invalid_callsign', 'not_in_log', 'unique_call')
```

## Export Formats

### Text File (.txt)
- Standard format shown above
- One file per station: `UBN_K1ABC.txt`
- Aggregate report: `UBN_SUMMARY.txt`

### CSV Export (.csv)
```csv
Callsign,UBN_Type,Band,Mode,DateTime,WorkedCall,SuggestedCall,Exchange_Sent,Exchange_Rcvd,Notes
K1ABC,UNIQUE,28MHz,SSB,2025-03-08 12:34,K9XYZ,,59 05,599 13,Not in any log
K1ABC,BUSTED,28MHz,SSB,2025-03-08 14:56,W1ZZZ,W1XXX,59 05,599 05,Similar to W1XXX
K1ABC,NIL,28MHz,CW,2025-03-08 18:34,LU5ABC,,599 05,599 13,LU5ABC has no record
```

### JSON Export (.json)
```json
{
  "callsign": "K1ABC",
  "log_id": 123,
  "contest": "SA10M 2025",
  "statistics": {
    "total_qsos": 234,
    "valid_qsos": 218,
    "unique_count": 8,
    "busted_count": 3,
    "nil_count": 4,
    "error_rate": 6.4
  },
  "entries": [
    {
      "type": "unique",
      "callsign": "K9XYZ",
      "band": "28MHz",
      "mode": "SSB",
      "timestamp": "2025-03-08T12:34:00Z"
    }
  ]
}
```

## Usage Example

```python
from src.services.cross_check_service import CrossCheckService
from src.services.ubn_report_generator import UBNReportGenerator

# Cross-check all logs
cross_check = CrossCheckService(db_session)
results = cross_check.check_all_logs(contest_id=1)

# Generate UBN reports
ubn_gen = UBNReportGenerator(db_session)

# Per-station reports
for log in logs:
    report = ubn_gen.generate_report(log.id)
    ubn_gen.export_text(report, f"reports/UBN_{log.callsign}.txt")

# Aggregate summary
summary = ubn_gen.generate_summary(contest_id=1)
ubn_gen.export_text(summary, "reports/UBN_SUMMARY.txt")
```

---

**Document Version**: 1.2  
**Created**: November 19, 2025  
**Updated**: April 7, 2026  
**Changes**:
- Corrected time tolerance from ±1 min to ±5 min
- Documented mode-aware busted-call detection (CW: Morse-weighted distance; PH: Jaro-Winkler)
- Added self-reference guard documentation
- Added cross-check reset mechanism documentation

