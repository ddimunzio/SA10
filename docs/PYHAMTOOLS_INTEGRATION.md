# PyHamtools Integration Guide

## Overview

**pyhamtools** is a Python library that provides ham radio utilities, particularly useful for:
- Callsign lookups (country, zone, DXCC entity)
- WPX prefix extraction
- Distance and bearing calculations
- Maidenhead grid locator utilities

## Installation

```bash
pip install pyhamtools
```

Already added to `requirements.txt`:
```
pyhamtools>=0.7.0
```

## What pyhamtools Provides for SA10M

### 1. **Automatic CQ Zone Lookup**

Instead of manually maintaining a CQ zone table, pyhamtools automatically determines the CQ zone from any callsign:

```python
from src.utils import get_cq_zone

zone = get_cq_zone("LU1HLH")  # Returns: 13
zone = get_cq_zone("W1AW")    # Returns: 5
zone = get_cq_zone("JA1RL")   # Returns: 25
```

### 2. **WPX Prefix Extraction**

Automatically extracts WPX prefixes for multiplier counting:

```python
from src.utils import extract_wpx_prefix

prefix = extract_wpx_prefix("LU1HLH")     # "LU1"
prefix = extract_wpx_prefix("W1AW")       # "W1"
prefix = extract_wpx_prefix("VE3/W1AW")   # "VE3" (portable operation)
prefix = extract_wpx_prefix("W1AW/4")     # "W1" (call/area)
prefix = extract_wpx_prefix("DL2025B")    # "DL2"
```

### 3. **Complete Callsign Information**

Get comprehensive information about any callsign:

```python
from src.utils import get_callsign_info

info = get_callsign_info("LU1HLH")

# Access all fields:
print(info.callsign)      # "LU1HLH"
print(info.prefix)        # "LU1"
print(info.country)       # "Argentina"
print(info.continent)     # "SA"
print(info.cq_zone)       # 13
print(info.itu_zone)      # 14
print(info.dxcc_entity)   # 100
print(info.latitude)      # -34.6037
print(info.longitude)     # -58.3816
```

### 4. **Callsign Validation**

Validate that callsigns have proper format:

```python
from src.utils import validate_callsign

validate_callsign("LU1HLH")    # True
validate_callsign("W1AW")      # True
validate_callsign("ABC123")    # True (format valid)
validate_callsign("INVALID")   # False (no digit)
validate_callsign("123")       # False (no letter)
```

### 5. **Distance and Bearing Calculations**

Calculate distances between grid squares:

```python
from src.utils import get_ham_utils

utils = get_ham_utils()
distance, bearing = utils.calculate_distance_and_bearing("FN31pr", "GG77xx")

print(f"Distance: {distance:.1f} km")
print(f"Bearing: {bearing:.1f}°")
```

## Integration with Database Models

### During Log Import (Cabrillo Parser)

When importing a contact from a Cabrillo log:

```python
from src.utils import get_callsign_info, extract_wpx_prefix
from src.database.models import Contact

# Parse QSO line from Cabrillo
# QSO:   28300 PH 2025-03-08 1207 LU1HLH  59 13  W1AW  59 5

call_received = "W1AW"
exchange_received = "59 5"  # Signal report + CQ zone

# Get callsign info automatically
info = get_callsign_info(call_received)

# Create contact record
contact = Contact(
    log_id=log_id,
    frequency=28300,
    mode="PH",
    call_received=call_received,
    exchange_received=exchange_received,
    
    # Automatically populated from pyhamtools:
    multiplier_type="cq_zone",
    multiplier_value=str(info.cq_zone),  # "5"
    
    # Also store WPX prefix as another multiplier
    # (will need second record or JSON field for both mults)
)
```

### During Scoring

```python
from src.utils import extract_wpx_prefix, get_callsign_info

# Count WPX prefix multipliers
wpx_prefixes = set()
cq_zones_10m = set()

for contact in contacts:
    # Extract WPX prefix
    prefix = extract_wpx_prefix(contact.call_received)
    wpx_prefixes.add(prefix)
    
    # Get CQ zone (from exchange or lookup)
    if contact.band == "10m":
        zone = contact.exchange_received.split()[-1]  # Last part is zone
        cq_zones_10m.add(zone)

wpx_mult_count = len(wpx_prefixes)
zone_mult_count = len(cq_zones_10m)
```

### During Validation

```python
from src.utils import validate_callsign, get_callsign_info

# Validate callsign format
if not validate_callsign(contact.call_received):
    contact.validation_status = ValidationStatus.INVALID_CALLSIGN
    contact.validation_notes = "Invalid callsign format"

# Verify exchange matches actual zone
info = get_callsign_info(contact.call_received)
claimed_zone = int(contact.exchange_received.split()[-1])

if info.cq_zone != claimed_zone:
    contact.validation_status = ValidationStatus.EXCHANGE_MISMATCH
    contact.validation_notes = f"Claimed zone {claimed_zone}, actual zone {info.cq_zone}"
```

## Advantages Over Manual Tables

### ❌ **Without pyhamtools**:
- Need to maintain CQ zone table (340+ DXCC entities × zones)
- Need to update when new entities are added
- Need manual WPX prefix extraction logic
- No validation of callsigns

### ✅ **With pyhamtools**:
- Automatic lookup of any callsign
- Always up-to-date with DXCC changes
- Handles portable operations automatically
- Built-in WPX prefix extraction
- Validates callsigns are real

## Fallback Mode

The `HamRadioUtils` class includes fallback logic if pyhamtools is not installed:

```python
# If pyhamtools not available:
# - Uses basic prefix-to-country mapping
# - Extracts WPX prefix with regex
# - Returns CallsignInfo with limited data
# - Logs warnings about missing features
```

This ensures the system works even without pyhamtools, but with reduced functionality.

## Database Schema Impact

The database schema **doesn't need to change** because:

1. **CQ zones** are stored in `exchange_received` field (as submitted)
2. **Validation** uses pyhamtools to verify exchanges
3. **Multipliers** are tracked in `multiplier_type`/`multiplier_value`
4. **No separate CQ zone table needed**

## Testing

Test the integration:

```bash
# Run the demo
python src/utils/ham_radio_utils.py LU1HLH

# Output:
# Looking up: LU1HLH
# 
# Callsign: LU1HLH
# WPX Prefix: LU1
# Country: Argentina
# Continent: SA
# CQ Zone: 13
# ITU Zone: 14
# DXCC Entity: 100
# Location: -34.6037, -58.3816
```

## Usage Examples

### Example 1: Import and Validate

```python
from src.utils import get_callsign_info, extract_wpx_prefix

# When importing a QSO
callsign = "LU1HLH"
exchange = "59 13"  # RS + Zone

# Validate the exchange
info = get_callsign_info(callsign)
claimed_zone = int(exchange.split()[-1])

if info.cq_zone != claimed_zone:
    print(f"Warning: {callsign} is in zone {info.cq_zone}, not {claimed_zone}")
```

### Example 2: Count Multipliers

```python
from src.utils import extract_wpx_prefix

# Count unique WPX prefixes
prefixes = set()
for contact in log.contacts:
    prefix = extract_wpx_prefix(contact.call_received)
    prefixes.add(prefix)

multiplier_count = len(prefixes)
```

### Example 3: Geographic Analysis

```python
from src.utils import get_callsign_info

# Analyze contacts by continent
continents = {}
for contact in log.contacts:
    info = get_callsign_info(contact.call_received)
    continent = info.continent
    continents[continent] = continents.get(continent, 0) + 1

print(continents)
# {'SA': 150, 'NA': 80, 'EU': 45, 'AS': 12}
```

## Summary

**pyhamtools** is extremely useful for:
- ✅ Automatic CQ zone lookups (no manual table needed)
- ✅ WPX prefix extraction
- ✅ Callsign validation
- ✅ DXCC entity identification
- ✅ Exchange validation
- ✅ Geographic analysis

**Integration points**:
1. **Log import** - Validate and enrich data
2. **Scoring** - Count multipliers automatically
3. **Validation** - Verify exchanges match reality
4. **Reports** - Add geographic statistics

The database schema remains unchanged - pyhamtools provides **runtime lookup capabilities** rather than static data.

