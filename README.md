# Ham Radio Contest Results Calculator

A Python application for calculating ham radio contest results with configurable rules and database persistence.

## Features

- 📝 Parse contest logs (Cabrillo, ADIF, CSV formats)
- 🏆 Calculate scores based on configurable contest rules
- 💾 Store contest history in database
- 📊 Generate detailed reports
- 🔧 Extensible rules engine for multiple contests
- ✅ Comprehensive log validation

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Initial Setup

```bash
# 1. Update DXCC data from CTY.DAT file (included: cty_wt.dat)
python update_dxcc_data.py

# 2. Create a contest (if needed)
python manage_contest.py create --name "SA10M 2025" --slug sa10m_2025 \
    --start "2025-03-08 00:00" --end "2025-03-09 23:59" \
    --rules config/contests/sa10m.yaml

# 3. Import contest logs
python import_logs.py --contest-id 1 --directory logs_sa10m_2025/
```

### Usage

```bash
# Process a contest log
python main.py process --contest sa10m --log path/to/log.cbr

# View results
python main.py results --contest sa10m --callsign LU1ABC

# List contests
python main.py contests list
```

## Project Status

🚧 **Under Development** - Phase 2 Complete

### Completed Phases

- ✅ **Phase 1: Foundation & Core Models** (Complete)
  - Database schema with SQLAlchemy
  - Pydantic data models
  - Reference data (CQ zones, DXCC entities)
  
- ✅ **Phase 2: Rules Engine** (Complete - Nov 17, 2025)
  - YAML-based contest configuration
  - Rules loader with Pydantic v2
  - Contest rules validator
  - Contact processing engine
  - WPX prefix extraction
  - Duplicate detection
  - Multiplier tracking
  - Score calculation
  - **17/17 tests passing ✓**

### Current Capabilities

```python
from src.core.rules import load_sa10m_rules, RulesEngine, Contact
from datetime import datetime

# Load SA10M contest rules
rules = load_sa10m_rules()

# Create rules engine
operator_info = {
    'callsign': 'LU1ABC',
    'continent': 'SA',
    'dxcc': 100,
    'cq_zone': 13
}
engine = RulesEngine(rules, operator_info)

# Process a contact
contact = Contact(
    timestamp=datetime.now(),
    callsign='W1AW',
    band='10m',
    mode='SSB',
    frequency=28500,
    rst_sent='59',
    rst_received='59',
    exchange_sent={'cq_zone': '13'},
    exchange_received={'cq_zone': '5'}
)

result = engine.process_contact(contact)
score = engine.calculate_final_score([result])
print(f"Final Score: {score['final_score']}")
```

### Next Phase

- 🔄 **Phase 3: Log Parsing** (In Progress)
  - Cabrillo parser
  - ADIF parser
  - CSV parser

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for complete roadmap.

## Supported Contests

- ✅ **SA10M Contest** (10 meter SA contest)
  - Exchange: RS/RST + CQ Zone (1-40)
  - Multipliers: WPX prefix (contest-wide), CQ zones (per-band)
  - Scoring: SA vs non-SA point values
  - Full rules: https://sa10m.com.ar/wp/rules/
- 🔜 More contests coming soon...

## Documentation

### Implementation & Progress
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Complete development roadmap
- [Phase 1 Completion](docs/PHASE_1_1_COMPLETION.md) - Database schema & models
- [Phase 2 Completion](docs/PHASE_2_COMPLETION.md) - Rules engine implementation

### Technical Documentation
- [Database Schema](docs/DATABASE_SCHEMA.md) - Complete database design
- [Database Quick Reference](docs/DATABASE_QUICK_REF.md) - Quick database guide
- [Rules Engine Quick Reference](docs/RULES_ENGINE_QUICK_REF.md) - Rules engine usage guide

### Contest Configuration
- [SA10M Contest Rules](config/contests/sa10m.yaml) - SA10M contest configuration
- [SA10M Documentation](docs/SA10M_UPDATE.md) - SA10M implementation details

### Getting Started
- [Getting Started Guide](docs/GETTING_STARTED.md) - Quick start tutorial
- Contest rules configuration guide (coming soon)
- User guide (coming soon)

## Technology Stack

- Python 3.10+
- SQLAlchemy (Database ORM)
- Pydantic (Data validation)
- PyYAML (Configuration)
- Click/Typer (CLI)
- pytest (Testing)

## License

MIT License

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Contact

For questions or suggestions, please open an issue on GitHub.

---

73! 📻

