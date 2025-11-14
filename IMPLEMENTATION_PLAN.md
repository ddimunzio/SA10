# Ham Radio Contest Results Calculator - Implementation Plan

## Project Overview
A Python application to calculate ham radio contest results, starting with SA10M contest rules, with extensible architecture for configurable contest rules and database persistence.

## Contest Rules Summary (SA10M)
Based on https://sa10m.com.ar/wp/rules/:
- **Objective**: Contact as many Argentine provinces as possible in 24 hours
- **Bands**: 10m (28 MHz)
- **Modes**: SSB and CW
- **Exchange**: Signal report + Province/Country code
- **Points System**: Different points for different contacts (province, country, etc.)
- **Multipliers**: Provinces worked
- **Final Score**: Total Points × Multipliers

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

## Phase 1: Foundation & Core Models (Week 1-2)

### 1.1 Project Setup ✅
- [x] Initialize Python project with virtual environment
- [x] Set up dependencies (SQLAlchemy, Pydantic, PyYAML, etc.)
- [x] Configure project structure
- [x] Set up logging framework
- [x] Initialize Git repository with .gitignore

### 1.2 Core Data Models
Create Pydantic models for:
- [ ] **Contact/QSO**: timestamp, callsign, band, mode, frequency, sent_report, received_report, exchange_sent, exchange_received
- [ ] **Station**: operator callsign, category, power, location
- [ ] **Log**: collection of contacts, metadata
- [ ] **Contest**: name, dates, rules reference
- [ ] **Score**: points breakdown, multipliers, final score

### 1.3 Database Schema
Design SQLAlchemy models:
- [ ] **contests** table: contest_id, name, start_date, end_date, rules_version
- [ ] **logs** table: log_id, contest_id, callsign, category, submitted_date
- [ ] **contacts** table: contact_id, log_id, timestamp, callsign, band, mode, exchange data
- [ ] **scores** table: score_id, log_id, total_points, multipliers, final_score
- [ ] **provinces/multipliers** table: reference data
- [ ] Set up Alembic for migrations

## Phase 2: Rules Engine (Week 3-4)

### 2.1 Rules Configuration Format
Design YAML schema for contest rules:
```yaml
contest:
  name: "SA10M"
  bands: ["10m"]
  modes: ["SSB", "CW"]
  duration_hours: 24
  
exchange:
  sent: ["rst", "province"]
  received: ["rst", "province"]
  
scoring:
  points:
    - condition: "same_country"
      value: 1
    - condition: "different_country"
      value: 3
  
  multipliers:
    type: "provinces"
    per_band: false
    per_mode: false
    
validation:
  min_rst: 111
  max_rst: 599
  duplicate_window: "same_band_mode"
```

### 2.2 Rules Engine Components
- [ ] **RulesLoader**: Parse YAML contest definitions
- [ ] **RulesValidator**: Validate rules configuration
- [ ] **RulesEngine**: Apply rules to contacts
- [ ] Create SA10M rules configuration
- [ ] Create base template for other contests

## Phase 3: Log Parsing (Week 5)

### 3.1 Cabrillo Parser
- [ ] Parse Cabrillo format header
- [ ] Parse QSO lines
- [ ] Extract contest metadata
- [ ] Validate format compliance

### 3.2 ADIF Parser (Optional)
- [ ] Parse ADIF format
- [ ] Map fields to internal model
- [ ] Handle various ADIF versions

### 3.3 CSV Parser
- [ ] Define CSV format specification
- [ ] Parse custom CSV format
- [ ] Flexible column mapping

## Phase 4: Validation & Scoring (Week 6-7)

### 4.1 Contact Validation
- [ ] Duplicate detection (same band/mode)
- [ ] Time validation (within contest period)
- [ ] Band validation
- [ ] Mode validation
- [ ] Exchange format validation
- [ ] Callsign format validation

### 4.2 Scoring Engine
- [ ] Point calculation based on rules
- [ ] Multiplier identification
- [ ] Duplicate handling
- [ ] Band/mode breakdown
- [ ] Generate score summary
- [ ] Handle contest-specific scoring logic

### 4.3 Cross-checking (Advanced)
- [ ] Match QSOs between stations
- [ ] Identify not-in-log (NIL) contacts
- [ ] Time/frequency discrepancies
- [ ] Exchange mismatches

## Phase 5: Database Integration (Week 8)

### 5.1 Repository Pattern
- [ ] **ContestRepository**: CRUD for contests
- [ ] **LogRepository**: Store and retrieve logs
- [ ] **ContactRepository**: Manage contacts
- [ ] **ScoreRepository**: Store scoring results

### 5.2 Data Persistence
- [ ] Save parsed logs to database
- [ ] Store scoring results
- [ ] Historical contest data
- [ ] Query and reporting functions

### 5.3 Database Migrations
- [ ] Initial schema migration
- [ ] Seed reference data (provinces, countries)
- [ ] Index optimization

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

### Parsing
- **python-dateutil**: Date/time handling
- **pyhamtools**: Callsign/DXCC utilities (optional)

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

#### reference_provinces
```sql
- id: INTEGER PRIMARY KEY
- code: VARCHAR(10) UNIQUE
- name: VARCHAR(100)
- country: VARCHAR(10)
```

## Configuration Example: SA10M Contest

```yaml
contest:
  name: "SA10M Contest"
  slug: "sa10m"
  description: "10 meter Argentine Provinces Contest"
  bands: 
    - "10m"
  modes:
    - "SSB"
    - "CW"
  duration_hours: 24
  
categories:
  - name: "Single Operator All Mode"
    code: "SOAB"
  - name: "Single Operator SSB"
    code: "SO-SSB"
  - name: "Single Operator CW"
    code: "SO-CW"
    
exchange:
  sent:
    - field: "rst"
      type: "signal_report"
    - field: "province"
      type: "code"
      validation: "province_code"
  received:
    - field: "rst"
      type: "signal_report"
    - field: "province"
      type: "code"

scoring:
  points:
    - description: "Own province"
      conditions:
        - type: "same_province"
      value: 0
    - description: "Different Argentine province"
      conditions:
        - type: "same_country"
        - type: "different_province"
      value: 2
    - description: "South American country"
      conditions:
        - type: "continent"
          value: "SA"
        - type: "different_country"
      value: 3
    - description: "Other continents"
      conditions:
        - type: "different_continent"
      value: 5
      
  multipliers:
    - type: "province"
      scope: "contest"  # Not per-band or per-mode
      applies_to: "argentine_provinces"
      
  final_score:
    formula: "points * multipliers"

validation:
  duplicate_window:
    type: "band_mode"
  exchange_format:
    rst: "^[1-5][1-9][1-9]$"
    province:
      - "BA", "CF", "CO", "CC", "CR", "ER", "FO", "JY", "LP", 
        "LR", "MZ", "MI", "NQ", "RN", "SA", "SJ", "SL", "SC",
        "SF", "SE", "TF", "TM", "DF"
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

**Document Version**: 1.0  
**Created**: November 13, 2025  
**Status**: Draft - Pending Review

