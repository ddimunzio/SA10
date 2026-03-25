# UBN Report Format Specification

**UBN**: Unique / Busted / Not-in-log Report  
**Purpose**: Identify errors in contest log submissions through cross-log validation

## UBN Report Structure

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
        but not within ±1 minute tolerance window

================================================================================
NOTES:
================================================================================

1. Time tolerance: ±1 minute for matching QSOs
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

```python
# Step 1: Get all submitted callsigns
submitted_calls = db.query("SELECT DISTINCT callsign FROM logs")

# Step 2: Get all worked calls that don't have logs
worked_not_submitted = db.query("""
    SELECT DISTINCT c.callsign
    FROM contacts c
    LEFT JOIN logs l ON l.callsign = c.callsign
    WHERE l.id IS NULL
""")

# Step 3: For each worked call, find similar submitted calls
from Levenshtein import distance

busted = []
for worked_call in worked_not_submitted:
    for submitted_call in submitted_calls:
        dist = distance(worked_call, submitted_call)
        if 1 <= dist <= 2:  # Close match
            # Check if submitted station has QSO with correct call
            has_qso = check_reciprocal_qso(submitted_call, log_id)
            busted.append({
                'logged_as': worked_call,
                'should_be': submitted_call,
                'distance': dist,
                'confirmed': has_qso
            })
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

**Document Version**: 1.0  
**Created**: November 19, 2025  
**Status**: Specification for Phase 4.3 Implementation

