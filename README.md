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

🚧 **Under Development** - See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for details.

## Supported Contests

- ✅ SA10M Contest (10 meter Argentine Provinces Contest)
- 🔜 More contests coming soon...

## Documentation

- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Detailed development roadmap
- [API Documentation](docs/api.md) - API reference (coming soon)
- [User Guide](docs/user_guide.md) - How to use the application (coming soon)
- [Contest Rules Configuration](docs/rules_config.md) - How to add new contests (coming soon)

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

