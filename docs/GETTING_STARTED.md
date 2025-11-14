# Getting Started - Ham Radio Contest Calculator

## Development Setup

### 1. Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (optional, for version control)

### 2. Initial Setup

```bash
# Navigate to project directory
cd C:\Users\lw5hr\proyects\SA10\pythonProject

# Activate virtual environment (should already be created)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python main.py
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_models.py -v
```

### 4. Project Structure

```
pythonProject/
├── src/                          # Source code
│   ├── core/                     # Core business logic
│   │   ├── models/              # Domain models (Pydantic)
│   │   │   └── contest.py       # ✅ Contest data models
│   │   ├── rules/               # ⏳ Rules engine
│   │   ├── scoring/             # ⏳ Scoring logic
│   │   └── validation/          # ⏳ Validation logic
│   ├── database/                # ⏳ Database layer (SQLAlchemy)
│   │   └── repositories/        # Data access
│   ├── parsers/                 # ⏳ Log file parsers
│   └── utils/                   # Utility functions
├── config/                      # Configuration files
│   └── contests/
│       └── sa10m.yaml          # ✅ SA10M contest rules
├── tests/                       # Test files
│   └── test_models.py          # ✅ Model tests
├── docs/                        # Documentation
├── main.py                      # ✅ Main entry point
├── requirements.txt             # ✅ Python dependencies
├── IMPLEMENTATION_PLAN.md       # ✅ Development roadmap
└── README.md                    # ✅ Project overview
```

## Current Status

### ✅ Completed
- [x] Project structure created
- [x] Dependencies defined
- [x] Core data models (Pydantic)
- [x] SA10M contest rules configuration
- [x] Basic unit tests
- [x] Development documentation

### ⏳ In Progress / Next Steps
Following the Implementation Plan phases:

**Phase 1: Foundation & Core Models** (Current)
- [x] Project setup
- [x] Core data models
- [ ] Database schema (SQLAlchemy models)
- [ ] Database migrations setup

**Phase 2: Rules Engine** (Next)
- [ ] YAML rules loader
- [ ] Rules validator
- [ ] Rules engine core

**Phase 3: Log Parsing**
- [ ] Cabrillo parser
- [ ] ADIF parser (optional)
- [ ] CSV parser

**Phase 4: Validation & Scoring**
- [ ] Contact validation
- [ ] Duplicate detection
- [ ] Points calculation
- [ ] Multiplier identification

## Development Workflow

### Adding a New Feature

1. **Review the Implementation Plan**
   - Check which phase the feature belongs to
   - Understand dependencies

2. **Create a Branch** (if using Git)
   ```bash
   git checkout -b feature/feature-name
   ```

3. **Write Tests First** (TDD approach)
   - Create test file in `tests/`
   - Write failing tests for the feature

4. **Implement the Feature**
   - Add code to appropriate module
   - Run tests frequently

5. **Validate**
   ```bash
   pytest
   python main.py  # Manual testing
   ```

6. **Document**
   - Add docstrings
   - Update README if needed

### Next Immediate Tasks

1. **Complete Phase 1: Database Models**
   ```python
   # Create: src/database/models.py
   # - SQLAlchemy models for contests, logs, contacts, scores
   # - Alembic migration configuration
   ```

2. **Create Initial Migration**
   ```bash
   alembic init alembic
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

3. **Build Repository Layer**
   ```python
   # Create: src/database/repositories/contest_repository.py
   # - CRUD operations for contests
   # - Query methods
   ```

## Common Commands

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_models.py::test_contact_creation -v

# Run with coverage report
pytest --cov=src --cov-report=html tests/
```

### Database (when implemented)
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running the Application
```bash
# Current (placeholder)
python main.py

# Future CLI commands (to be implemented)
python main.py process --log path/to/log.cbr --contest sa10m
python main.py score --log-id 123
python main.py export --contest sa10m --format html
```

## Key Concepts

### Contest Models (Pydantic)
- **Contact**: Single QSO with validation
- **Station**: Operator information
- **ContestLog**: Complete log submission
- **ScoreBreakdown**: Calculated results

### Rules Configuration (YAML)
- Defines contest-specific rules
- Scoring logic
- Validation rules
- Exchange format

### Database Models (SQLAlchemy) - To be implemented
- Persistent storage
- Historical tracking
- Query optimization

## Tips for Development

1. **Follow the Implementation Plan**: It's structured to build features in logical order
2. **Write Tests First**: Helps clarify requirements
3. **Use Type Hints**: Already established in models, continue the practice
4. **Document As You Go**: Clear docstrings help future development
5. **Keep Models Separate**: Pydantic for business logic, SQLAlchemy for persistence

## Resources

### Ham Radio Contest Standards
- Cabrillo format: http://www.kkn.net/~trey/cabrillo/
- ADIF specification: https://adif.org/
- SA10M rules: https://sa10m.com.ar/wp/rules/

### Python Libraries Documentation
- SQLAlchemy: https://docs.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- Alembic: https://alembic.sqlalchemy.org/
- Click: https://click.palletsprojects.com/
- pytest: https://docs.pytest.org/

## Questions?

Refer to:
- `IMPLEMENTATION_PLAN.md` for architecture and roadmap
- `README.md` for project overview
- Code docstrings for API details

---

Happy coding! 73! 📻

