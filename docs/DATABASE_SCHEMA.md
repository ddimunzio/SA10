# Database Schema Documentation

## Overview

The SA10 Contest Management System uses a relational database to store contest logs, QSO contacts, scores, and reference data. The schema is designed to fully support the **Cabrillo log format v3.0 specification** while providing efficient querying and validation capabilities.

## Database Schema

### Core Tables

#### 1. **contests**
Stores contest definition and metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(100) | Contest name (e.g., "SA10M Contest") |
| slug | VARCHAR(50) | URL-friendly identifier (unique) |
| start_date | DATETIME | Contest start date/time (UTC) |
| end_date | DATETIME | Contest end date/time (UTC) |
| rules_file | VARCHAR(200) | Path to YAML rules file |
| created_at | DATETIME | Record creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `slug`

---

#### 2. **logs**
Stores Cabrillo log submissions with header information.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| contest_id | INTEGER | Foreign key to contests.id |
| cabrillo_version | VARCHAR(10) | Cabrillo format version (default: "3.0") |
| callsign | VARCHAR(20) | Station callsign (required) |
| location | VARCHAR(50) | Location code (DX, SA, etc.) |
| club | VARCHAR(100) | Club affiliation |
| contest_name | VARCHAR(100) | CONTEST field from Cabrillo |
| **Category Fields** | | |
| category_operator | VARCHAR(50) | SINGLE-OP, MULTI-OP, etc. |
| category_assisted | VARCHAR(50) | ASSISTED, NON-ASSISTED |
| category_band | VARCHAR(20) | 10M, ALL, etc. |
| category_mode | VARCHAR(20) | SSB, CW, MIXED |
| category_power | VARCHAR(20) | HIGH, LOW, QRP |
| category_station | VARCHAR(50) | FIXED, MOBILE, PORTABLE |
| category_transmitter | VARCHAR(20) | ONE, TWO, etc. |
| category_overlay | VARCHAR(50) | TB-WIRES, ROOKIE, etc. |
| category_time | VARCHAR(20) | 6-HOURS, 12-HOURS, etc. |
| **Operator Info** | | |
| operators | TEXT | Comma-separated operator callsigns |
| name | VARCHAR(200) | Operator name |
| address | TEXT | Full street address |
| address_city | VARCHAR(100) | City |
| address_state_province | VARCHAR(100) | State/Province |
| address_postalcode | VARCHAR(20) | Postal code |
| address_country | VARCHAR(100) | Country |
| grid_locator | VARCHAR(10) | Maidenhead grid locator |
| email | VARCHAR(200) | Email address |
| **Score & Processing** | | |
| claimed_score | INTEGER | Claimed score from log |
| created_by | VARCHAR(200) | Logging software (e.g., N1MM Logger+) |
| submitted_at | DATETIME | Submission timestamp |
| file_path | TEXT | Original file path |
| file_hash | VARCHAR(64) | SHA256 hash for duplicate detection |
| status | ENUM | pending, validated, scored, published, error |
| validation_notes | TEXT | Validation errors/warnings |
| processed_at | DATETIME | Processing timestamp |
| metadata | JSON | Additional Cabrillo fields |
| created_at | DATETIME | Record creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Composite index on `(contest_id, callsign)`
- Index on `status`
- Index on `file_hash`

**Relationships:**
- Many logs belong to one contest
- One log has many contacts
- One log has one score

---

#### 3. **contacts**
Stores individual QSO/contact records from Cabrillo QSO lines.

**Cabrillo QSO Format:**
```
QSO: freq mo date time call-sent rst-sent exch-sent call-rcvd rst-rcvd exch-rcvd t
QSO:   28300 PH 2025-03-08 1207 CE1KR         59   12   DP7D          59   14
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| log_id | INTEGER | Foreign key to logs.id |
| **QSO Details** | | |
| frequency | INTEGER | Frequency in kHz (required) |
| mode | VARCHAR(10) | PH (SSB), CW, RY (RTTY), DG (Digital) |
| qso_date | VARCHAR(10) | Date in YYYY-MM-DD format |
| qso_time | VARCHAR(4) | Time in HHMM UTC format |
| qso_datetime | DATETIME | Combined datetime for queries |
| **Transmitter (Sent)** | | |
| call_sent | VARCHAR(20) | Own callsign |
| rst_sent | VARCHAR(10) | Signal report sent |
| exchange_sent | VARCHAR(50) | Exchange data sent (province/zone) |
| **Receiver (Received)** | | |
| call_received | VARCHAR(20) | Other station's callsign |
| rst_received | VARCHAR(10) | Signal report received |
| exchange_received | VARCHAR(50) | Exchange data received |
| transmitter_id | VARCHAR(5) | Multi-transmitter ID (0, 1, etc.) |
| **Derived Fields** | | |
| band | VARCHAR(10) | Derived from frequency (10m, 20m, etc.) |
| **Scoring** | | |
| points | INTEGER | Points awarded for this QSO |
| is_multiplier | BOOLEAN | Is this a new multiplier? |
| multiplier_type | VARCHAR(50) | Type (province, country, zone) |
| multiplier_value | VARCHAR(50) | Value (e.g., "BA", "W") |
| **Validation** | | |
| is_valid | BOOLEAN | Is this QSO valid? |
| is_duplicate | BOOLEAN | Is this a duplicate? |
| duplicate_of_id | INTEGER | FK to first occurrence |
| validation_status | ENUM | valid, duplicate, invalid_callsign, etc. |
| validation_notes | TEXT | Validation error details |
| **Cross-checking** | | |
| matched_contact_id | INTEGER | FK to matching contact in other log |
| time_diff_seconds | INTEGER | Time difference with matched contact |
| frequency_diff_khz | INTEGER | Frequency difference |
| **Metadata** | | |
| metadata | JSON | Additional fields |
| created_at | DATETIME | Record creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Validation Status Values:**
- `valid` - Contact is valid
- `duplicate` - Duplicate contact on same band/mode
- `invalid_callsign` - Malformed callsign
- `invalid_exchange` - Invalid exchange data
- `out_of_period` - QSO outside contest period
- `invalid_band` - Invalid band for contest
- `invalid_mode` - Invalid mode for contest
- `not_in_log` - Not found in other station's log
- `time_mismatch` - Significant time difference with matched contact
- `exchange_mismatch` - Exchange data mismatch

**Indexes:**
- Primary key on `id`
- Index on `log_id`
- Index on `qso_datetime`
- Index on `call_received`
- Composite index on `(band, mode)`
- Index on `is_valid`
- Index on `is_duplicate`
- Composite index on `(log_id, qso_datetime)`
- **Unique constraint** on `(log_id, qso_datetime, call_received, band, mode)` to prevent true duplicates

---

#### 4. **scores**
Stores calculated scores and detailed breakdowns.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| log_id | INTEGER | Foreign key to logs.id (unique) |
| **QSO Statistics** | | |
| total_qsos | INTEGER | Total QSOs in log |
| valid_qsos | INTEGER | Valid QSOs |
| duplicate_qsos | INTEGER | Duplicate QSOs |
| invalid_qsos | INTEGER | Invalid QSOs |
| not_in_log_qsos | INTEGER | Not-in-log QSOs |
| **Scoring** | | |
| total_points | INTEGER | Total points before multipliers |
| multipliers | INTEGER | Number of multipliers worked |
| final_score | INTEGER | Final score (points × multipliers) |
| **Detailed Breakdowns (JSON)** | | |
| points_by_band | JSON | `{"10m": 1000, "20m": 500}` |
| points_by_mode | JSON | `{"CW": 800, "SSB": 700}` |
| points_by_type | JSON | `{"same_country": 200, "different_country": 1500}` |
| qsos_by_band | JSON | `{"10m": 50, "20m": 30}` |
| qsos_by_mode | JSON | `{"CW": 40, "SSB": 40}` |
| qsos_by_hour | JSON | `{"12": 10, "13": 15, ...}` |
| **Multipliers Detail** | | |
| multipliers_list | JSON | `["BA", "CF", "CO", "W", "K", ...]` |
| multipliers_by_band | JSON | Per-band multipliers (if applicable) |
| multipliers_by_mode | JSON | Per-mode multipliers (if applicable) |
| validation_errors | JSON | `{"duplicate": 5, "invalid_exchange": 2}` |
| **Rankings** | | |
| rank_overall | INTEGER | Overall rank |
| rank_category | INTEGER | Rank within category |
| rank_country | INTEGER | Rank within country |
| **Metadata** | | |
| calculated_at | DATETIME | Calculation timestamp |
| calculation_version | VARCHAR(20) | Scoring algorithm version |
| notes | TEXT | Additional notes |
| created_at | DATETIME | Record creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `log_id`
- Index on `final_score` (for leaderboards)

---

### Reference Tables

#### 5. **reference_provinces**
Argentine provinces and other location codes for validation.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| code | VARCHAR(10) | Province code (BA, CF, CO, etc.) - unique |
| name | VARCHAR(100) | Full name (Buenos Aires, etc.) |
| country | VARCHAR(10) | Country code (AR for Argentina) |
| region | VARCHAR(50) | Optional regional grouping |
| is_active | BOOLEAN | For historical provinces |
| created_at | DATETIME | Record creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `code`
- Index on `country`

---

#### 6. **reference_dxcc**
DXCC entities/countries for scoring and validation.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| prefix | VARCHAR(10) | Callsign prefix (LU, W, K, etc.) - unique |
| entity_code | INTEGER | DXCC entity number |
| entity_name | VARCHAR(100) | Country name |
| continent | VARCHAR(2) | SA, NA, EU, AS, AF, OC |
| itu_zone | INTEGER | ITU zone number |
| cq_zone | INTEGER | CQ zone number |
| is_deleted | BOOLEAN | For deleted DXCC entities |
| created_at | DATETIME | Record creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Unique index on `prefix`
- Index on `entity_code`
- Index on `continent`

---

#### 7. **audit_logs**
Audit trail for tracking changes and operations.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| entity_type | VARCHAR(50) | Log, Contact, Score |
| entity_id | INTEGER | ID of affected entity |
| action | VARCHAR(50) | INSERT, UPDATE, DELETE, VALIDATE, SCORE |
| user | VARCHAR(100) | Who performed the action |
| changes | JSON | What changed |
| timestamp | DATETIME | When the action occurred |

**Indexes:**
- Primary key on `id`
- Composite index on `(entity_type, entity_id)`
- Index on `timestamp`

---

## Entity Relationships

```
contests (1) ─────< (N) logs
                        │
                        ├─────< (N) contacts
                        │
                        └─────< (1) scores

contacts (1) ────< (N) contacts (self-referencing for duplicates and matches)
```

## Cabrillo Format Mapping

### Header Fields Mapping

| Cabrillo Field | Database Column |
|----------------|-----------------|
| START-OF-LOG | cabrillo_version |
| LOCATION | location |
| CALLSIGN | callsign |
| CLUB | club |
| CONTEST | contest_name |
| CATEGORY-OPERATOR | category_operator |
| CATEGORY-ASSISTED | category_assisted |
| CATEGORY-BAND | category_band |
| CATEGORY-MODE | category_mode |
| CATEGORY-POWER | category_power |
| CATEGORY-STATION | category_station |
| CATEGORY-TRANSMITTER | category_transmitter |
| CATEGORY-OVERLAY | category_overlay |
| CATEGORY-TIME | category_time |
| CLAIMED-SCORE | claimed_score |
| OPERATORS | operators |
| NAME | name |
| ADDRESS | address |
| ADDRESS-CITY | address_city |
| ADDRESS-STATE-PROVINCE | address_state_province |
| ADDRESS-POSTALCODE | address_postalcode |
| ADDRESS-COUNTRY | address_country |
| GRID-LOCATOR | grid_locator |
| EMAIL | email |
| CREATED-BY | created_by |

### QSO Line Mapping

```
QSO:   28300 PH 2025-03-08 1207 CE1KR         59   12   DP7D          59   14
       │     │  │          │    │             │    │    │             │    │
       │     │  │          │    │             │    │    │             │    └─ exchange_received
       │     │  │          │    │             │    │    │             └────── rst_received
       │     │  │          │    │             │    │    └──────────────────── call_received
       │     │  │          │    │             │    └───────────────────────── exchange_sent
       │     │  │          │    │             └────────────────────────────── rst_sent
       │     │  │          │    └──────────────────────────────────────────── call_sent
       │     │  │          └───────────────────────────────────────────────── qso_time
       │     │  └──────────────────────────────────────────────────────────── qso_date
       │     └─────────────────────────────────────────────────────────────── mode
       └───────────────────────────────────────────────────────────────────── frequency
```

## Key Design Decisions

### 1. **Duplicate Detection**
- Unique constraint on `(log_id, qso_datetime, call_received, band, mode)` prevents accidental duplicates
- `is_duplicate` flag marks duplicate QSOs within a log
- `duplicate_of_id` points to the first valid occurrence

### 2. **Cross-Log Validation**
- `matched_contact_id` links to corresponding QSO in other station's log
- `time_diff_seconds` and `frequency_diff_khz` store discrepancies
- Enables "not-in-log" detection and exchange verification

### 3. **JSON Fields for Flexibility**
- `metadata` in logs and contacts stores uncommon Cabrillo fields
- Score breakdowns use JSON for detailed analysis
- Allows schema evolution without migrations

### 4. **Performance Optimizations**
- Composite indexes on frequently queried columns
- Denormalized `band` field (derived from frequency) for faster filtering
- Pre-calculated `qso_datetime` for time-based queries

### 5. **Data Integrity**
- Foreign key constraints ensure referential integrity
- Enums restrict status values to valid options
- Timestamps track all changes

## Usage Examples

### Creating a Contest
```python
contest = Contest(
    name="SA10M Contest 2025",
    slug="sa10m-2025",
    start_date=datetime(2025, 3, 8, 12, 0, 0),
    end_date=datetime(2025, 3, 9, 12, 0, 0),
    rules_file="config/contests/sa10m_2025.yaml"
)
```

### Inserting a Log
```python
log = Log(
    contest_id=1,
    callsign="LU1HLH",
    category_band="10M",
    category_mode="MIXED",
    claimed_score=402720
)
```

### Adding a Contact
```python
contact = Contact(
    log_id=1,
    frequency=28300,
    mode="PH",
    qso_date="2025-03-08",
    qso_time="1207",
    qso_datetime=datetime(2025, 3, 8, 12, 7, 0),
    call_sent="LU1HLH",
    rst_sent="59",
    exchange_sent="13",
    call_received="DP7D",
    rst_received="59",
    exchange_received="14",
    band="10m"
)
```

---

## Validation Rules Implementation

The database schema supports the following validation rules (Point 4.3):

1. **Bad Exchanges**: Check `exchange_received` against `reference_provinces` and `reference_dxcc`
2. **Bad Calls**: Validate `call_received` format and check against known prefixes
3. **Out of Contest Period**: Compare `qso_datetime` with contest `start_date` and `end_date`
4. **Duplicates**: Detect via unique constraint and `is_duplicate` flag
5. **Not in Log**: Cross-reference using `matched_contact_id`
6. **Time/Frequency Mismatches**: Store differences in `time_diff_seconds` and `frequency_diff_khz`

