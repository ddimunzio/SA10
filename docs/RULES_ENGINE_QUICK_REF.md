# Rules Engine Quick Reference

## Quick Start

```python
from src.core.rules import load_sa10m_rules, RulesEngine, Contact
from datetime import datetime

# 1. Load contest rules
rules = load_sa10m_rules()

# 2. Set up operator info
operator_info = {
    'callsign': 'LU1ABC',
    'continent': 'SA',
    'dxcc': 100,
    'cq_zone': 13
}

# 3. Create rules engine
engine = RulesEngine(rules, operator_info)

# 4. Process contacts
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

# 5. Calculate score
contacts = [result]  # All processed contacts
score = engine.calculate_final_score(contacts)

print(f"Final Score: {score['final_score']}")
```

## Loading Rules

```python
from src.core.rules import RulesLoader, load_sa10m_rules

# Method 1: Convenience function
rules = load_sa10m_rules()

# Method 2: Using loader
loader = RulesLoader()
rules = loader.load_contest('sa10m')

# List available contests
contests = loader.list_contests()

# Get contest info
info = loader.get_contest_info('sa10m')
```

## Validating Rules

```python
from src.core.rules import RulesValidator, validate_contest_rules

# Method 1: Using validator class
validator = RulesValidator(rules)
is_valid, errors, warnings = validator.validate()

if not is_valid:
    for error in errors:
        print(f"Error: {error}")

# Method 2: Convenience function
result = validate_contest_rules(rules)
print(f"Valid: {result['valid']}")
print(f"Errors: {result['error_count']}")
print(f"Warnings: {result['warning_count']}")

# Validate individual exchange values
is_valid, error = validator.validate_exchange_value('cq_zone', '13', 'SSB')
```

## Creating Contacts

```python
from src.core.rules import Contact
from datetime import datetime

contact = Contact(
    timestamp=datetime.now(),
    callsign='W1AW',           # Worked station
    band='10m',                # Band
    mode='SSB',                # Mode
    frequency=28500,           # Frequency in kHz
    rst_sent='59',             # Signal report sent
    rst_received='59',         # Signal report received
    exchange_sent={'cq_zone': '13'},      # Your exchange
    exchange_received={'cq_zone': '5'}    # Their exchange
)
```

## Processing Contacts

```python
# Create engine
engine = RulesEngine(rules, operator_info)

# Process single contact
result = engine.process_contact(contact)

# Check results
print(f"Points: {result.points}")
print(f"Duplicate: {result.is_duplicate}")
print(f"Multiplier: {result.is_multiplier}")
print(f"Mult Types: {result.multiplier_types}")
```

## Calculating Scores

```python
# Process all contacts
processed_contacts = [engine.process_contact(c) for c in contacts]

# Calculate final score
score = engine.calculate_final_score(processed_contacts)

# Access score breakdown
print(f"Total QSOs: {score['total_qsos']}")
print(f"Valid QSOs: {score['valid_qsos']}")
print(f"Duplicates: {score['duplicate_qsos']}")
print(f"Total Points: {score['total_points']}")
print(f"WPX Mults: {score['wpx_multipliers']}")
print(f"Zone Mults: {score['zone_multipliers']}")
print(f"Final Score: {score['final_score']}")

# Per-band breakdown
for band, band_score in score['band_scores'].items():
    print(f"\n{band}:")
    print(f"  QSOs: {band_score['qsos']}")
    print(f"  Points: {band_score['points']}")
    print(f"  Zone Mults: {band_score['zone_mults']}")
    print(f"  Score: {band_score['score']}")
```

## Operator Info Dictionary

```python
operator_info = {
    'callsign': 'LU1ABC',      # Your callsign
    'continent': 'SA',          # Your continent (SA, NA, EU, AS, AF, OC, AN)
    'dxcc': 100,               # Your DXCC entity code
    'cq_zone': 13              # Your CQ zone (1-40)
}
```

## WPX Prefix Extraction

```python
# Extract WPX prefix from callsign
prefix = engine._extract_wpx_prefix('W1AW')      # Returns: 'W1'
prefix = engine._extract_wpx_prefix('LU3DRP')    # Returns: 'LU3'
prefix = engine._extract_wpx_prefix('9A3YT')     # Returns: '9A3'
```

## SA10M Scoring Rules

### Points
| Contact Type | Points |
|-------------|--------|
| Same DXCC entity | 0 |
| SA → non-SA station | 4 |
| SA → SA station (different DXCC) | 2 |
| non-SA → SA station | 4 |
| non-SA → non-SA station | 2 |

### Multipliers
1. **WPX Prefix** - Each unique prefix (contest-wide)
2. **CQ Zone** - Each unique zone per band

### Final Score Formula
```
Per Band Score = QSO Points × (WPX Prefix Mults + CQ Zone Mults for that band)
Final Score = Sum of all band scores
```

### Example Calculation
```
10m Band:
  - 10 QSOs = 50 points
  - 3 WPX prefixes (W1, K3, CE7)
  - 2 CQ zones (5, 12)
  
10m Score = 50 × (3 + 2) = 250

If only 10m band was worked:
Final Score = 250
```

## Duplicate Detection

SA10M uses **band_mode** duplicate window:
- Same callsign on same band AND mode = Duplicate (0 points)
- Same callsign on different mode = New QSO ✓
- Same callsign on different band = New QSO ✓

```python
# First contact
contact1 = Contact(..., callsign='W1AW', band='10m', mode='SSB', ...)
result1 = engine.process_contact(contact1)  # is_duplicate = False

# Duplicate - same band, same mode
contact2 = Contact(..., callsign='W1AW', band='10m', mode='SSB', ...)
result2 = engine.process_contact(contact2)  # is_duplicate = True, points = 0

# Not duplicate - different mode
contact3 = Contact(..., callsign='W1AW', band='10m', mode='CW', ...)
result3 = engine.process_contact(contact3)  # is_duplicate = False
```

## Common Patterns

### Process Log File (Conceptual)

```python
# After implementing log parser in Phase 3:
from src.core.rules import load_sa10m_rules, RulesEngine
from src.parsers import CabrilloParser  # Future

# Load rules and parse log
rules = load_sa10m_rules()
parser = CabrilloParser()
log_data = parser.parse('path/to/log.cbr')

# Create engine with operator from log
operator_info = {
    'callsign': log_data.callsign,
    'continent': log_data.continent,
    'dxcc': log_data.dxcc,
    'cq_zone': log_data.cq_zone
}
engine = RulesEngine(rules, operator_info)

# Process all contacts
results = [engine.process_contact(c) for c in log_data.contacts]

# Calculate score
score = engine.calculate_final_score(results)
```

### Custom Scoring Conditions

To add custom scoring conditions, extend `_evaluate_condition()` in RulesEngine:

```python
# In rules_engine.py
def _evaluate_condition(self, condition, contact):
    # ... existing conditions ...
    
    # Add custom condition
    elif cond_type == 'my_custom_condition':
        # Your logic here
        return some_boolean_result
```

## Testing

```bash
# Run all rules engine tests
python -m pytest tests/test_rules_engine.py -v

# Run specific test class
python -m pytest tests/test_rules_engine.py::TestRulesEngine -v

# Run specific test
python -m pytest tests/test_rules_engine.py::TestRulesEngine::test_wpx_prefix_extraction -v
```

## Troubleshooting

### Issue: Rules file not found
```python
# Make sure you're in the project root directory
# Or specify the full path to config/contests/
loader = RulesLoader(Path('/full/path/to/config/contests'))
```

### Issue: Validation errors
```python
# Check what's wrong with the rules
validator = RulesValidator(rules)
is_valid, errors, warnings = validator.validate()
for error in errors:
    print(error)
```

### Issue: Wrong points calculated
```python
# Check which scoring rule matched
for rule in rules.scoring.points:
    if engine._evaluate_conditions(rule.conditions, contact):
        print(f"Matched: {rule.description} = {rule.value} points")
        break
```

## API Reference

### Contact
```python
Contact(
    timestamp: datetime,
    callsign: str,
    band: str,
    mode: str,
    frequency: int,
    rst_sent: str,
    rst_received: str,
    exchange_sent: Dict[str, str],
    exchange_received: Dict[str, str],
    operator_info: Optional[Dict[str, Any]] = None
)

# Calculated fields (set by RulesEngine):
contact.points: int
contact.is_duplicate: bool
contact.is_multiplier: bool
contact.multiplier_types: List[str]
contact.validation_errors: List[str]
```

### RulesEngine
```python
engine = RulesEngine(rules: ContestRules, operator_info: Dict[str, Any])

# Methods
engine.process_contact(contact: Contact) -> Contact
engine.calculate_final_score(contacts: List[Contact]) -> Dict[str, Any]

# Properties
engine.worked_prefixes: Set[str]
engine.worked_zones_per_band: Dict[str, Set[str]]
engine.worked_calls: Dict[str, List[Contact]]
```

### Score Dictionary
```python
{
    'total_qsos': int,
    'valid_qsos': int,
    'duplicate_qsos': int,
    'total_points': int,
    'wpx_multipliers': int,
    'zone_multipliers': int,
    'zone_mults_per_band': Dict[str, int],
    'band_scores': Dict[str, Dict],
    'final_score': int
}
```

---

**Last Updated:** November 17, 2025  
**See Also:** `docs/PHASE_2_COMPLETION.md`

