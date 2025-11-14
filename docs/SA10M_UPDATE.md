# SA10M Contest Configuration - Update Summary

## Changes Made

The SA10M contest configuration has been updated to correctly reflect the actual contest rules:

### ✅ Exchange Format Updated

**Previous (Incorrect):**
- Exchange: RST + Province Code (e.g., "599 CF")

**Current (Correct):**
- Exchange for SSB: RS (2 digits) + CQ Zone (e.g., "59 13")
- Exchange for CW: RST (3 digits) + CQ Zone (e.g., "599 13")

### ✅ Scoring Updated

**Previous (Incorrect):**
- Based on Argentine provinces
- Multipliers: Argentine provinces worked

**Current (Correct):**
- Based on CQ zones
- Points:
  - Same CQ zone: 1 point (2 points for CW)
  - Different CQ zone, same continent: 2 points (4 points for CW)
  - Different continent: 3 points (6 points for CW)
- Multipliers: Each unique CQ zone worked counts as 1 multiplier
- Final Score: Total Points × Multipliers

### ✅ Validation Rules Updated

**Signal Reports:**
- SSB: RS format with 2 digits (pattern: `^[1-5][1-9]$`)
  - Examples: "59", "57", "55"
- CW: RST format with 3 digits (pattern: `^[1-5][1-9][1-9]$`)
  - Examples: "599", "579", "559"

**CQ Zones:**
- Valid range: 1-40
- Pattern: `^([1-9]|[1-3][0-9]|40)$`

### ✅ Reference Data Updated

**CQ Zones relevant to SA10M Contest:**
- Zone 13: Argentina (primary)
- Zones 9-12: Other South American countries
- Zones 1-5: North America
- Zones 14-15: Europe
- Full range: 1-40 (all zones valid)

## Updated Code Components

### 1. Configuration File
**File:** `config/contests/sa10m.yaml`
- Updated exchange format
- Updated scoring rules
- Updated validation patterns
- Updated reference data

### 2. Core Models
**File:** `src/core/models/contest.py`
- Updated `Contact.validate_rst()` to accept both 2-digit (RS) and 3-digit (RST) formats
- Updated example data to use CQ zones instead of provinces
- Updated all model examples (Contact, Station, ContestLog, ScoreBreakdown)

### 3. Unit Tests
**File:** `tests/test_models.py`
- Updated all test data to use CQ zones
- Updated RS/RST values (2 digits for SSB, 3 for CW)
- Added new tests:
  - `test_rs_validation_ssb()` - Validates 2-digit RS for SSB
  - `test_rst_validation_cw()` - Validates 3-digit RST for CW
  - `test_invalid_rst_four_digits()` - Ensures 4+ digits are rejected

**Total Tests: 10** (previously 7)

## Example QSO Data

### SSB Contact Example
```python
Contact(
    timestamp=datetime(2025, 11, 13, 14, 30, 0),
    frequency=28500,
    mode=ModeEnum.SSB,
    callsign="LU1ABC",
    rst_sent="59",        # 2 digits for SSB
    exchange_sent="13",    # CQ Zone 13 (Argentina)
    rst_received="59",
    exchange_received="11", # CQ Zone 11 (Brazil)
    band=BandEnum.BAND_10M
)
```

### CW Contact Example
```python
Contact(
    timestamp=datetime(2025, 11, 13, 14, 35, 0),
    frequency=28500,
    mode=ModeEnum.CW,
    callsign="LU3ABC",
    rst_sent="599",       # 3 digits for CW
    exchange_sent="13",   # CQ Zone 13 (Argentina)
    rst_received="599",
    exchange_received="12", # CQ Zone 12 (Chile)
    band=BandEnum.BAND_10M
)
```

## Verification Steps

To verify the changes:

1. **Check configuration:**
   ```bash
   cat config/contests/sa10m.yaml
   ```

2. **Run tests:**
   ```bash
   python -m pytest tests/test_models.py -v
   ```

3. **Validate models:**
   ```bash
   python -c "from src.core.models.contest import Contact, ModeEnum; from datetime import datetime; c = Contact(timestamp=datetime.now(), frequency=28500, mode=ModeEnum.SSB, callsign='LU1ABC', rst_sent='59', exchange_sent='13', rst_received='59', exchange_received='11'); print('Valid:', c.callsign)"
   ```

## Implementation Status

✅ **Completed:**
- SA10M configuration file updated
- Core models updated to handle RS/RST
- Unit tests updated with correct data
- Validation logic updated
- Documentation updated

⏳ **Next Steps:**
- Continue with Phase 1: Database models
- Implement rules engine to parse YAML configuration
- Create parsers for Cabrillo format

## Notes

- Argentina is primarily in CQ Zone 13
- Most SA10M participants will exchange zone 13
- The contest focuses on 10m band only
- Both SSB and CW modes are allowed
- CW contacts receive double points

---

**Updated:** November 13, 2025  
**Status:** Configuration Complete ✅

