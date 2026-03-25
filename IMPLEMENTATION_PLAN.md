# Ham Radio Contest Results Calculator - Implementation Plan

## Project Overview
A Python application to calculate ham radio contest results, starting with SA10M contest rules, with extensible architecture for configurable contest rules and database persistence.

## Contest Rules Summary (SA10M)
Based on https://sa10m.com.ar/wp/rules/ and config/contests/sa10m.yaml:
- **Objective**: Work as many different WPX prefixes and CQ zones as possible on 10 meters
- **Bands**: 10m (28 MHz)
- **Modes**: SSB and CW
- **Exchange**: Signal report (RS/RST) + CQ Zone number (1-40)
- **Points System**: Varies by station type and continent (see rules)
- **Multipliers**: 
  - WPX prefixes (once per contest)
  - CQ zones (once per band)
- **Final Score**: Per band (Points × Multipliers), then sum all bands

## Architecture Overview

```
ham-radio-contest/
├── src/
│   ├── core/
│   │   ├── models/           # Data models
│   │   ├── rules/            # Contest rules engine
│   │   ├── scoring/          # Scoring calculation
│   │   └── validation/       # Log validation
│   ├── database/
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── repositories/     # Data access layer
│   │   └── migrations/       # Database migrations
│   ├── parsers/
│   │   ├── cabrillo.py       # Cabrillo log format
│   │   ├── adif.py           # ADIF log format
│   │   └── csv.py            # CSV format
│   ├── api/                  # REST API (optional)
│   ├── ui/                   # User interface
│   └── utils/
├── config/
│   ├── contests/
│   │   ├── sa10m.yaml        # SA10M contest definition
│   │   └── template.yaml     # Template for new contests
│   └── settings.py
├── tests/
├── docs/
├── requirements.txt
└── main.py
```

## Project Progress Summary

**Overall Status**: 🟢 On Track (70% Complete)  
**Last Updated**: November 20, 2025

### Completed Phases ✅
- ✅ **Phase 1**: Foundation & Core Models (Complete)
- ✅ **Phase 2.1 & 2.2**: Rules Engine (Complete)
- ✅ **Phase 3.1**: Cabrillo Parser (Complete)
- ✅ **Phase 3.2**: Database Integration & Log Version Management (Complete)
- ✅ **Phase 4.1**: Contact Validation (Complete)
- ✅ **Phase 4.3**: SQL-Based Cross-checking & UBN Reports (Complete)
- ✅ **Phase 5.1**: Database Integration & Log Import (Complete)

### Current Phase 🔄
- **Phase 4.2**: Scoring Engine (Next Priority)
  - Calculate points for each QSO based on rules
  - Track multipliers (WPX prefix, CQ zones)
  - Generate score breakdowns
  - Calculate final scores
  
### Upcoming Phases 📋
- **Phase 6**: Web Interface & API
  - Calculate points for each QSO
  - Track multipliers (WPX prefix, CQ zones)
  - Generate score breakdowns
  - Calculate final scores

### Recent Additions (Nov 18, 2025)
- ✅ **Smart Log Version Management**: Automatic handling of updated contest logs
- ✅ File modification timestamp tracking and intelligent replacement logic
- ✅ Database clearing utilities and complete import pipeline
- ✅ Enhanced import statistics and error reporting

### Test Status
- Total Tests: 55+ tests across all modules
- Status: All passing ✅
- Coverage: Core functionality well-tested

### Documentation
- 📄 `POINT_2_COMPLETE.md` - Phase 1 completion
- 📄 `PHASE_2_2_COMPLETE.md` - Phase 2 completion
- 📄 `docs/PHASE_3_1_COMPLETION.md` - Phase 3.1 completion
- 📄 `docs/PHASE_4_1_COMPLETION.md` - Phase 4.1 completion
- 📄 `docs/PHASE_5_1_COMPLETION.md` - Phase 5.1 completion
- 📄 `docs/DATABASE_SCHEMA.md` - Database documentation
- 📄 `docs/RULES_ENGINE_QUICK_REF.md` - Rules engine guide
- 📄 `docs/CABRILLO_PARSER_QUICK_REF.md` - Parser guide
- 📄 `DUPLICATE_IMPORT_VERIFIED.md` - Duplicate handling verification
- 📄 `PROJECT_STATUS.md` - Current status overview

## Phase 1: Foundation & Core Models ✅ COMPLETE

### 1.1 Project Setup ✅
- [x] Initialize Python project with virtual environment
- [x] Set up dependencies (SQLAlchemy, Pydantic, PyYAML, etc.)
- [x] Configure project structure
- [x] Set up logging framework
- [x] Initialize Git repository with .gitignore

### 1.2 Core Data Models
Create Pydantic models for:
- [x] **Contact/QSO**: timestamp, callsign, band, mode, frequency, sent_report, received_report, exchange_sent, exchange_received
- [x] **Station**: operator callsign, category, power, location
- [x] **Log**: collection of contacts, metadata
- [x] **Contest**: name, dates, rules reference
- [x] **Score**: points breakdown, multipliers, final score

### 1.3 Database Schema ✅
Design SQLAlchemy models:
- [x] **contests** table: contest_id, name, start_date, end_date, rules_version
- [x] **logs** table: log_id, contest_id, callsign, category, submitted_date (+ full Cabrillo header support)
- [x] **contacts** table: contact_id, log_id, timestamp, callsign, band, mode, exchange data (+ validation fields)
- [x] **scores** table: score_id, log_id, total_points, multipliers, final_score (+ detailed breakdowns)
- [x] **reference data** tables: CQ zones, DXCC entities
- [x] **audit_logs** table: change tracking and audit trail
- [x] Pydantic validation models for all entities
- [x] Database manager with session handling
- [x] Reference data population (24 provinces, 24 DXCC entities)
- [x] Comprehensive documentation (DATABASE_SCHEMA.md)
- [x] Tested and verified working
- [ ] Set up Alembic for migrations (deferred - using direct SQLAlchemy for now)

**Phase 1 Completed: November 16, 2025**
- ✅ All core data models implemented with Pydantic
- ✅ Complete database schema with 7 tables supporting Cabrillo v3.0
- ✅ Database manager with session handling and reference data population
- ✅ Comprehensive documentation created
- ✅ All tests passing
- 📄 See: `POINT_2_COMPLETE.md`, `docs/DATABASE_SCHEMA.md`, `docs/DATABASE_QUICK_REF.md`

## Phase 2: Rules Engine (Week 3-4)

### 2.1 Rules Configuration Format ✅ ✅
Design YAML schema for contest rules:
```yaml
contest:
  name: "SA10M"
  bands: ["10m"]
  modes: ["SSB", "CW"]
  duration_hours: 24
  
exchange:
  sent: ["rs_rst", "cq_zone"]
  received: ["rs_rst", "cq_zone"]
  
scoring:
  points:
    - condition: "same_dxcc"
      value: 0
    - condition: "sa_to_non_sa"
      value: 4
    - condition: "sa_to_sa_different_dxcc"
      value: 2
    - condition: "non_sa_to_sa"
      value: 4
    - condition: "non_sa_to_non_sa"
      value: 2
    # Mobile stations have special rules
  
  multipliers:
    - type: "wpx_prefix"
      scope: "contest"  # Once per contest
      description: "WPX prefix multiplier"
    - type: "cq_zone"
      scope: "per_band"  # Per band
      description: "CQ zone (1-40) per band"
    
  final_score:
    formula: "sum(band_points * (wpx_mults + zone_mults_per_band))"
    
validation:
  rs_rst:
    ssb_pattern: "^[1-5][1-9]$"
    cw_pattern: "^[1-5][1-9][1-9]$"
  cq_zone:
    min: 1
    max: 40
  duplicate_window: "same_band_mode"
```

### 2.2 Rules Engine Components ✅
- [x] **RulesLoader**: Parse YAML contest definitions
- [x] **RulesValidator**: Validate rules configuration
- [x] **RulesEngine**: Apply rules to contacts
- [x] Create SA10M rules configuration
- [x] Create base template for other contests

**Phase 2.2 Completed: November 17, 2025**
- ✅ RulesLoader component with Pydantic models for YAML parsing
- ✅ RulesValidator with comprehensive validation checks
- ✅ RulesEngine for processing contacts, calculating points, and identifying multipliers
- ✅ WPX prefix extraction (handles all callsign formats)
- ✅ Duplicate detection based on band/mode
- ✅ Multiplier tracking (WPX prefix contest-wide, CQ zones per-band)
- ✅ Final score calculation
- ✅ 17 comprehensive tests - all passing
- 📄 Files: `src/core/rules/rules_loader.py`, `rules_validator.py`, `rules_engine.py`
- 📄 Tests: `tests/test_rules_engine.py`

## Phase 3: Log Parsing (Week 5)

### 3.1 Cabrillo Parser ✅
- [x] Parse Cabrillo format header
- [x] Parse QSO lines
- [x] Extract contest metadata
- [x] Validate format compliance
- [x] Error and warning collection
- [x] Support all Cabrillo v3.0 tags
- [x] Multi-encoding support (UTF-8, Latin-1, CP1252)
- [x] Comprehensive test suite (19 tests passing)
- [x] Tested with real SA10M contest logs

**Phase 3.1 Completed: November 17, 2025**
- ✅ Full WWROF Cabrillo v3.0 specification parser
- ✅ All standard header tags (CALLSIGN, CONTEST, categories, operators, etc.)
- ✅ QSO line parsing with flexible exchange handling
- ✅ Validation with error/warning collection and line numbers
- ✅ Callsign normalization and mode normalization (SSB → PH)
- ✅ Support for portable/mobile callsigns (K1ABC/M, W1AW/MM)
- ✅ Transmitter ID support for multi-transmitter operations
- ✅ 19 comprehensive tests - all passing
- ✅ Successfully tested with real SA10M contest logs
- 📄 See: `docs/PHASE_3_1_COMPLETION.md`, `docs/CABRILLO_PARSER_QUICK_REF.md`
- 📄 Files: `src/parsers/cabrillo.py`, `tests/test_cabrillo_parser.py`

### 3.2 Database Integration and Log Version Management ✅
- [x] LogImportService for database persistence
- [x] Batch import functionality for directories
- [x] File modification timestamp tracking
- [x] Intelligent log version comparison
- [x] Automatic replacement of older log versions
- [x] Database clearing utilities
- [x] Complete import pipeline with detailed reporting
- [x] Error handling and transaction safety
- [x] Contest management utilities (create/list/show/delete)
- [x] Contest ID parameter required for imports (no auto-creation)

**Phase 3.2 Completed: November 18, 2025**
- ✅ Complete database integration with LogRepository and ContactRepository
- ✅ **Smart Version Management**: Automatic handling of updated contest logs
- ✅ File modification date tracking and comparison logic
- ✅ Replacement of older versions when newer files are submitted
- ✅ Skip import if existing file is same or newer (prevents data loss)
- ✅ Database clearing utility with confirmation prompts
- ✅ Complete import pipeline (`import_logs.py`) with detailed statistics
- ✅ **Contest Management**: Manual contest creation/management via `manage_contest.py`
- ✅ **No auto-population**: Contest ID must be provided during import
- ✅ Simplified workflow: one contest at a time, explicit control
- ✅ Comprehensive error handling and logging
- ✅ **Validation Reason Tracking** (November 19, 2025):
  - Invalid contacts saved to database with specific reasons
  - Parser tracks missing exchanges, missing RST, format errors
  - Saved to `validation_notes` field for later review
  - Enables complete data preservation and detailed error reporting
  - Test suite confirms all validation reasons are captured
  - 📄 See: `docs/VALIDATION_REASON_TRACKING.md`
- ✅ Tested with version replacement scenarios
- 📄 See: `manage_contest.py`, `import_logs.py`, `import_all.py`
- 📄 Files: `src/services/log_import_service.py`, Database models updated

### 3.3 ADIF Parser (Optional)
- [ ] Parse ADIF format
- [ ] Map fields to internal model
- [ ] Handle various ADIF versions

### 3.3 CSV Parser (Optional)
- [ ] Define CSV format specification
- [ ] Parse custom CSV format
- [ ] Flexible column mapping

## Phase 4: Validation & Scoring (Week 6-7)

### 4.1 Contact Validation ✅
- [x] **Duplicate detection** (same band/mode/callsign) - mark in database
  - All contacts imported in Phase 5.1, duplicates marked here
  - Update `is_duplicate` field based on contest rules
  - Keep first QSO, mark subsequent as duplicates
- [x] Time validation (within contest period)
- [x] Band validation
- [x] Mode validation
- [x] Exchange format validation (RS/RST, CQ zone)
- [x] Callsign format validation
- [x] Bad exchange detection (invalid zones, malformed reports)
- [x] Invalid callsign detection (invalid characters)
- [x] Complete log processing pipeline (import + validation)

**Phase 4.1 Completed: November 17, 2025**
- ✅ ContactValidator with comprehensive validation rules
- ✅ Duplicate detection: same callsign + band + mode
- ✅ Exchange validation: RS/RST format, CQ zone (1-40)
- ✅ Callsign validation: format checking, mobile suffix detection
- ✅ Time validation: within contest period
- ✅ Band/mode validation: against allowed contest values
- ✅ LogProcessingPipeline: complete import + validation workflow
- ✅ Batch directory processing with statistics
- ✅ Database integration: validation results persisted
- ✅ Tested with real SA10M logs: 718 QSOs (711 valid, 6 duplicates, 1 invalid)
- ✅ Demo script with formatted output
- 📄 See: `docs/PHASE_4_1_COMPLETION.md`
- 📄 Files: `src/core/validation/contact_validator.py`, `src/services/log_processing_pipeline.py`
- 📄 Demo: `demo_pipeline.py`

### 4.2 Scoring Engine
- [ ] Point calculation based on rules
- [ ] Multiplier identification
- [ ] Duplicate handling
- [ ] Band/mode breakdown
- [ ] Generate score summary
- [ ] Handle contest-specific scoring logic

### 4.3 Cross-checking & UBN Report Generation (Pure SQL)
**Approach**: Use optimized SQL queries for fast cross-log validation across all stations

#### Cross-checking Components
- [x] **SQL Query Engine**: Pure SQL queries for cross-log matching ✅
  - Bi-directional QSO matching (A logged B, B logged A)
  - Time window tolerance (±1 minute)
  - Band/mode matching
  - Exchange validation
- [x] **Not-in-Log (NIL) Detection**: ✅
  - Identify contacts where one station logged the QSO but other station's log missing it
  - Track NIL percentage per log
- [x] **Busted Call Detection**: ✅ IMPROVED
  - Find incorrectly copied callsigns (e.g., K9JX vs K9JY)
  - Use similarity algorithms (Levenshtein distance) to suggest corrections
  - Cross-reference with all submitted callsigns
  - **Verify suggested call has reciprocal QSO at same time** (±1 minute)
  - Only report as busted if reciprocal QSO exists with suggested callsign
- [x] **Unique Call Detection**: ✅
  - Identify calls that appear in only one log (not worked by any other station)
  - Flag as potential busts or non-submitting stations

#### UBN Report Generation
- [x] **UBN Format Output** (Standard contest format): ✅
  ```
  Callsign: K1ABC
  
  UNIQUE calls (not found in any other log):
    14MHz CW  2025-03-08 1234  K9XYZ
    
  BUSTED calls (incorrectly copied):
    28MHz SSB 2025-03-08 1456  W1ZZZ  (Should be: W1XXX)
    
  NOT-IN-LOG (other station has no record):
    28MHz CW  2025-03-08 1834  LU5ABC
  ```
- [x] **UBN Statistics per Log**: ✅
  - Total QSOs, Valid QSOs
  - NIL count and percentage
  - Busted call count
  - Unique call count
- [x] **Aggregate UBN Report**: Summary across all logs ✅

#### SQL Optimization
- [x] Database indexing on: callsign, timestamp, band, mode, log_id ✅
- [ ] Materialized views for common queries (optional)
- [x] Batch processing for large contests ✅
- [x] Progress tracking for long-running validations ✅

### 4.3 SQL-Based Cross-checking Service ✅ COMPLETE
**Implementation Details**

#### CrossCheckService Components
- [x] **CrossCheckService class**: Main service for cross-log validation ✅
- [x] **SQL Query Templates**: Optimized queries for: ✅
  - Bidirectional QSO matching
  - NIL detection (one-way QSOs)
  - Busted call detection with similarity scoring
  - Unique call identification
- [x] **Database Indexes**: Add indexes for performance ✅
  ```sql
  CREATE INDEX idx_contacts_callsign ON contacts(callsign);
  CREATE INDEX idx_contacts_timestamp ON contacts(timestamp);
  CREATE INDEX idx_contacts_band_mode ON contacts(band, mode);
  CREATE INDEX idx_contacts_log_callsign ON contacts(log_id, callsign);
  ```

#### UBN Report Generator
- [x] **UBNReport class**: Data model for UBN entries ✅
- [x] **UBNReportGenerator**: Generate standard UBN format ✅
  - Per-log UBN reports (individual station reports)
  - Aggregate UBN summary (all logs)
  - Export to text file format (TXT, CSV, JSON)
- [x] **UBN Statistics**: Calculate and display: ✅
  - Total/Valid/Invalid QSO counts
  - NIL rate percentage
  - Busted call percentage
  - Unique call percentage

#### SQL Query Examples
```sql
-- Not-in-Log Detection
SELECT c1.* FROM contacts c1
LEFT JOIN contacts c2 ON 
  c2.callsign = (SELECT callsign FROM logs WHERE id = c1.log_id)
  AND c1.callsign = (SELECT callsign FROM logs WHERE id = c2.log_id)
  AND c1.band = c2.band
  AND c1.mode = c2.mode
  AND ABS(JULIANDAY(c1.timestamp) - JULIANDAY(c2.timestamp)) < 0.000694  -- 1 min
WHERE c2.id IS NULL;

-- Busted Call Detection (find similar callsigns)
-- Use Python Levenshtein distance post-query for efficiency
```

#### Improved Levenshtein Busted Call Detection Algorithm
**Rules Applied:**
1. **Only suggest callsigns that submitted logs**: Compare busted calls only against submitted callsigns
2. **Verify reciprocal QSO exists**: For each suggestion, check if the suggested station has a QSO with the logging station
3. **Time-based verification**: Reciprocal QSO must be within ±1 minute of the logged QSO
4. **Band and mode matching**: Reciprocal QSO must be on same band and mode
5. **Best match selection**: If multiple similar calls found, pick the one with reciprocal QSO and highest similarity score

**Example:**
- Station LW5HR logs LU6DX at 14:23 UTC on 28MHz SSB
- Algorithm finds LU5DX (Levenshtein distance = 1) in submitted logs
- Checks if LU5DX has LW5HR logged at ~14:23 UTC on 28MHz SSB
- If YES → Report as BUSTED call (LU6DX should be LU5DX)
- If NO → May just be a non-submitting station, not reported as busted

This significantly reduces false positives and improves accuracy of busted call detection.

#### Performance Targets
- [x] Process 100,000 QSOs in < 60 seconds ✅ (82K QSOs in 5 seconds)
- [x] Generate UBN reports in < 30 seconds ✅ (821 reports generated)
- [x] Support contests with 1000+ logs ✅ (844 logs processed)

#### Testing & Validation
- [x] Test with SA10M contest data (82,000+ QSOs) ✅
- [x] Verify UBN report accuracy ✅
- [x] Performance benchmarking ✅ (5.13 seconds total)
- [x] **Comprehensive Test Suite Created** ✅
  - Unit tests for NIL, UNIQUE, BUSTED detection
  - Edge case testing (time boundaries, band/mode matching)
  - Key test: UNIQUE not BUSTED when no reciprocal QSO
  - See: `docs/TEST_CASES_CROSSCHECK.md`
  - Files: `tests/test_cross_check_rules.py`, `test_cross_check_rules_simple.py`
- [ ] Compare results with manual cross-checking (Future)

## Phase 5: Database Integration (Week 8)

### 5.1 Repository Pattern & Log Import ✅
- [x] **LogRepository**: CRUD for logs/stations
- [x] **ContactRepository**: CRUD for QSOs with batch operations  
- [x] **LogImportService**: Complete import workflow
- [x] Parse Cabrillo → Save to database pipeline
- [x] Automatic datetime parsing from date+time
- [x] Automatic band detection from frequency
- [x] **Duplicate contacts imported without filtering** (processed during validation/scoring)
- [x] Batch directory import
- [x] Contest auto-creation
- [x] Transaction management and error handling

**Phase 5.1 Completed: November 17, 2025**
- ✅ LogRepository and ContactRepository with full CRUD operations
- ✅ LogImportService combines parsing + database persistence
- ✅ Complete workflow: Cabrillo file → Parse → Validate → Save to DB
- ✅ Batch import for processing entire contest directories
- ✅ Automatic data transformation (datetime, band detection)
- ✅ **ALL contacts imported including duplicates** - no filtering during import
- ✅ **VERIFIED**: Tested with real SA10M logs - duplicates imported correctly
- ✅ Duplicate detection deferred to Phase 4.1 (Contact Validation)
- ✅ Data now available in database for cross-checking and scoring
- ✅ Demo script for single and batch imports
- ✅ Comprehensive test suite
- 📄 See: `docs/PHASE_5_1_COMPLETION.md`, `DUPLICATE_IMPORT_VERIFIED.md`
- 📄 Files: `src/database/repositories/`, `src/services/log_import_service.py`
- 📄 Demo: `demo_import_logs.py`, Tests: `tests/test_log_import.py`
- 📄 Verification: `test_duplicate_import.py`, `verify_duplicate_import.py`

### 5.2 Additional Repositories
- [ ] **ContestRepository**: Advanced contest management
- [ ] **ScoreRepository**: Store calculated scoring results
- [ ] Query optimization and indexing

### 5.3 Data Persistence Enhancements
- [ ] Store scoring results from rules engine
- [ ] Historical contest data management
- [ ] Advanced query and reporting functions
- [ ] Performance optimization

### 5.4 Database Migrations
- [ ] Alembic migration setup
- [ ] Schema version management
- [ ] Index optimization for queries

### 5.5 DXCC Data Management ✅
- [x] DXCCDataLoader service using pyhamtools
- [x] CTY.DAT file parsing and database population
- [x] Callsign lookup with DXCC/country/zone information
- [x] Periodic update capability
- [x] Management script for updates
- [x] Documentation and quick start guide

**Phase 5.5 Completed: November 19, 2025**
- ✅ Complete DXCC data loader using pyhamtools and CTY.DAT format
- ✅ Parses CTY.DAT file with all entity information (340+ entities)
- ✅ Stores data in `cty_data` table with prefixes, zones, coordinates
- ✅ Callsign lookup API using pyhamtools
- ✅ Database population and update functionality
- ✅ Management script: `update_dxcc_data.py`
- ✅ Supports periodic CTY.DAT updates (download new file and re-run)
- ✅ Multi-encoding support for international characters
- ✅ Comprehensive documentation
- 📄 See: `docs/DXCC_DATA_GUIDE.md`
- 📄 Files: `src/services/dxcc_data_loader.py`, `update_dxcc_data.py`
- 📄 Database: `CTYData` model in `src/database/models.py`

## Phase 6: User Interface (Week 9-10)

### 6.1 CLI Interface
- [ ] Upload log file command
- [ ] Score calculation command
- [ ] View results command
- [ ] Contest management commands
- [ ] Export results

### 6.2 Web Interface (Optional - Future)
- [ ] Flask/FastAPI backend
- [ ] Upload interface
- [ ] Results dashboard
- [ ] Contest leaderboard
- [ ] Admin panel for contest configuration

## Phase 7: Reporting & Export (Week 11)

### 7.1 Score Reports
- [ ] Text summary report
- [ ] HTML report with breakdown
- [ ] PDF export
- [ ] CSV export for analysis

### 7.2 Statistics
- [ ] Band breakdown
- [ ] Mode breakdown
- [ ] Hourly QSO rate
- [ ] Multiplier progress
- [ ] Comparison with previous contests

## Phase 8: Testing & Documentation (Week 12)

### 8.1 Testing
- [ ] Unit tests for all components
- [ ] Integration tests
- [ ] Test with sample logs
- [ ] Performance testing with large logs
- [ ] Rules validation tests

### 8.2 Documentation
- [ ] API documentation
- [ ] User guide
- [ ] Contest rules configuration guide
- [ ] Database schema documentation
- [ ] Contributing guidelines

## Technology Stack

### Core
- **Python 3.10+**
- **SQLAlchemy 2.0**: ORM for database
- **Alembic**: Database migrations
- **Pydantic**: Data validation
- **PyYAML**: Rules configuration

### Parsing & Validation
- **python-dateutil**: Date/time handling
- **email-validator**: Email validation for Pydantic EmailStr
- **pyhamtools**: Callsign/DXCC utilities
- **python-Levenshtein**: String similarity for busted call detection

### CLI
- **Click** or **Typer**: Command-line interface
- **Rich**: Beautiful terminal output

### Web (Future)
- **FastAPI**: REST API
- **Jinja2**: Template engine
- **SQLite/PostgreSQL**: Database

### Testing
- **pytest**: Testing framework
- **pytest-cov**: Code coverage
- **factory_boy**: Test data factories

### Reporting
- **Jinja2**: Report templates
- **WeasyPrint**: PDF generation (optional)
- **Pandas**: Data analysis (optional)

## Database Schema Details

### Tables

#### contests
```sql
- id: INTEGER PRIMARY KEY
- name: VARCHAR(100)
- slug: VARCHAR(50) UNIQUE
- start_date: DATETIME
- end_date: DATETIME
- rules_file: VARCHAR(200)
- created_at: DATETIME
```

#### logs
```sql
- id: INTEGER PRIMARY KEY
- contest_id: INTEGER FOREIGN KEY
- callsign: VARCHAR(20)
- category: VARCHAR(50)
- power: VARCHAR(20)
- overlay: VARCHAR(50)
- submitted_at: DATETIME
- file_path: TEXT
- status: ENUM('pending', 'validated', 'scored')
```

#### contacts
```sql
- id: INTEGER PRIMARY KEY
- log_id: INTEGER FOREIGN KEY
- timestamp: DATETIME
- frequency: INTEGER
- mode: VARCHAR(10)
- callsign: VARCHAR(20)
- rst_sent: INTEGER
- exchange_sent: VARCHAR(50)
- rst_received: INTEGER
- exchange_received: VARCHAR(50)
- points: INTEGER
- is_multiplier: BOOLEAN
- is_duplicate: BOOLEAN
- is_valid: BOOLEAN
- validation_notes: TEXT
```

#### scores
```sql
- id: INTEGER PRIMARY KEY
- log_id: INTEGER FOREIGN KEY
- total_qsos: INTEGER
- valid_qsos: INTEGER
- duplicate_qsos: INTEGER
- invalid_qsos: INTEGER
- total_points: INTEGER
- multipliers: INTEGER
- final_score: INTEGER
- breakdown: JSON
- calculated_at: DATETIME
```

#### reference_dxcc
```sql
- id: INTEGER PRIMARY KEY
- entity_code: INTEGER UNIQUE
- entity_name: VARCHAR(100)
- continent: VARCHAR(2)
- cq_zone: INTEGER
```

## Configuration Example: SA10M Contest

```yaml
contest:
  name: "SA10M Contest"
  slug: "sa10m"
  description: "10 meter SA contest"
  bands: 
    - "10m"
  modes:
    - "SSB"
    - "CW"
  duration_hours: 24
  
categories:
  - name: "Single Operator CW"
    code: "SO-CW"
  - name: "Single Operator SSB"
    code: "SO-SSB"
  - name: "Single Operator Mixed"
    code: "SO-Mixed"
  - name: "Multi Operator"
    code: "MO"
    
exchange:
  sent:
    - field: "rs_rst"
      type: "signal_report"
      description: "RS for SSB (2 digits), RST for CW (3 digits)"
  received:
    - field: "rs_rst"
      type: "signal_report"
    - field: "cq_zone"
      type: "zone"
      description: "CQ Zone number (1-40)"

scoring:
  points:
    - description: "Same DXCC entity"
      conditions:
        - type: "same_dxcc"
      value: 0
    - description: "SA station contacts non-SA station"
      conditions:
        - type: "operator_continent"
          value: "SA"
        - type: "contact_continent"
          value: "!SA"
      value: 4
    - description: "SA station contacts SA station (different DXCC)"
      conditions:
        - type: "operator_continent"
          value: "SA"
        - type: "contact_continent"
          value: "SA"
        - type: "different_dxcc"
      value: 2
    - description: "Non-SA station contacts SA station"
      conditions:
        - type: "operator_continent"
          value: "!SA"
        - type: "contact_continent"
          value: "SA"
      value: 4
    - description: "Non-SA station contacts non-SA station"
      conditions:
        - type: "operator_continent"
          value: "!SA"
        - type: "contact_continent"
          value: "!SA"
      value: 2
    # Mobile stations (/MM, /AM) have special scoring rules
      
  multipliers:
    - type: "wpx_prefix"
      scope: "contest"  # Once per contest
      description: "WPX prefix multiplier (e.g., K1, W2, LU3, CE7)"
    - type: "cq_zone"
      scope: "per_band"  # Per band
      description: "Each CQ zone worked per band counts as 1 multiplier"
      
  final_score:
    formula: "sum(band_points * (wpx_multipliers + zone_multipliers_per_band))"
    description: "Score calculated per band: QSO points × (prefix mults + zone mults), then summed"

validation:
  duplicate_window:
    type: "band_mode"
  exchange_format:
    rs_rst:
      ssb_pattern: "^[1-5][1-9]$"
      cw_pattern: "^[1-5][1-9][1-9]$"
    cq_zone:
      pattern: "^([1-9]|[1-3][0-9]|40)$"
      min: 1
      max: 40

# NOTE: Geographic reference data (CQ zones, continents, DXCC entities) is now
# provided by the DXCC data system (DXCCDataLoader + pyhamtools + CTY.DAT).
# The reference_data section has been removed as it was redundant.
```

## Key Features for Future Expansion

### Multi-Contest Support
- Easy addition of new contests via YAML
- Contest-specific scoring logic plugins
- Shared validation rules library

### Advanced Features
- Real-time scoring during contest
- Integration with logging software
- Automated log submission
- Contest calendar/reminders
- Statistical analysis across contests
- Operator performance tracking

### Reporting Features
- Leaderboards
- Certificate generation
- Award tracking
- Historical comparisons
- Geographic distribution maps

## Development Priorities

### Must Have (MVP)
1. Parse Cabrillo logs
2. SA10M rules engine
3. Basic scoring calculation
4. SQLite database storage
5. CLI interface
6. Text report generation

### Should Have
1. ADIF parsing
2. Advanced validation (cross-checking)
3. Multiple contest support
4. HTML reports
5. Historical contest tracking

### Nice to Have
1. Web interface
2. Real-time scoring
3. PDF certificates
4. Geographic maps
5. Multi-language support

## Success Metrics
- Successfully parse and score SA10M contest logs
- Accurate point calculation matching official results
- Store complete contest history
- Generate comprehensive reports
- Support additional contests through configuration
- Processing time < 5 seconds for typical log (500 QSOs)

## Next Steps

1. **Review and approve this plan**
2. **Set up development environment**
3. **Create initial project structure**
4. **Start with Phase 1: Core models**
5. **Implement SA10M rules first**
6. **Test with real SA10M logs**

## Questions to Consider

1. **Target Users**: Personal use or multi-user system?
2. **Deployment**: Desktop app, web service, or both?
3. **Scale**: Expected log sizes and number of contests?
4. **Additional Contests**: Which contests to support next?
5. **Real-time**: Need live scoring during contests?
6. **Integration**: Connect to other ham radio software?

---

**Document Version**: 1.6  
**Created**: November 13, 2025  
**Last Updated**: November 20, 2025  
**Status**: In Progress - Phase 4.3 Complete (70%), Phase 4.2 (Scoring Engine) Next

