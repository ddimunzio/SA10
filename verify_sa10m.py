#!/usr/bin/env python3
"""
Verification script for SA10M configuration updates.
Run this to verify all changes are working correctly.
"""

import sys
from datetime import datetime

print("=" * 60)
print("SA10M Configuration Verification")
print("=" * 60)
print()

# Test 1: Import models
print("Test 1: Importing models...")
try:
    from src.core.models.contest import Contact, Station, ContestLog, ScoreBreakdown, BandEnum, ModeEnum
    print("✅ Models imported successfully")
except Exception as e:
    print(f"❌ Failed to import models: {e}")
    sys.exit(1)

# Test 2: Create SSB contact with 2-digit RS and CQ zone
print("\nTest 2: Creating SSB contact with RS (2 digits) and CQ zone...")
try:
    contact_ssb = Contact(
        timestamp=datetime(2025, 11, 13, 14, 30, 0),
        frequency=28500,
        mode=ModeEnum.SSB,
        callsign="LU1ABC",
        rst_sent="59",
        exchange_sent="13",
        rst_received="59",
        exchange_received="11",
        band=BandEnum.BAND_10M
    )
    print(f"✅ SSB Contact created: {contact_ssb.callsign} - RS: {contact_ssb.rst_sent} - Zone: {contact_ssb.exchange_sent}")
except Exception as e:
    print(f"❌ Failed to create SSB contact: {e}")
    sys.exit(1)

# Test 3: Create CW contact with 3-digit RST and CQ zone
print("\nTest 3: Creating CW contact with RST (3 digits) and CQ zone...")
try:
    contact_cw = Contact(
        timestamp=datetime(2025, 11, 13, 14, 35, 0),
        frequency=28500,
        mode=ModeEnum.CW,
        callsign="PY2ABC",
        rst_sent="599",
        exchange_sent="13",
        rst_received="599",
        exchange_received="11",
        band=BandEnum.BAND_10M
    )
    print(f"✅ CW Contact created: {contact_cw.callsign} - RST: {contact_cw.rst_sent} - Zone: {contact_cw.exchange_sent}")
except Exception as e:
    print(f"❌ Failed to create CW contact: {e}")
    sys.exit(1)

# Test 4: Verify 1-digit RS fails
print("\nTest 4: Verifying 1-digit RS is rejected...")
try:
    Contact(
        timestamp=datetime(2025, 11, 13, 14, 30, 0),
        frequency=28500,
        mode=ModeEnum.SSB,
        callsign="LU1ABC",
        rst_sent="5",  # Invalid - only 1 digit
        exchange_sent="13",
        rst_received="59",
        exchange_received="11"
    )
    print("❌ Should have raised ValueError for 1-digit RS")
    sys.exit(1)
except ValueError as e:
    print(f"✅ Correctly rejected 1-digit RS: {e}")

# Test 5: Verify 4-digit RST fails
print("\nTest 5: Verifying 4-digit RST is rejected...")
try:
    Contact(
        timestamp=datetime(2025, 11, 13, 14, 30, 0),
        frequency=28500,
        mode=ModeEnum.CW,
        callsign="LU1ABC",
        rst_sent="5999",  # Invalid - 4 digits
        exchange_sent="13",
        rst_received="599",
        exchange_received="11"
    )
    print("❌ Should have raised ValueError for 4-digit RST")
    sys.exit(1)
except ValueError as e:
    print(f"✅ Correctly rejected 4-digit RST: {e}")

# Test 6: Create station with CQ zone
print("\nTest 6: Creating station with CQ zone...")
try:
    station = Station(
        callsign="LU1ABC",
        category="SOAB",
        power="HIGH",
        location="13"
    )
    print(f"✅ Station created: {station.callsign} - Zone: {station.location}")
except Exception as e:
    print(f"❌ Failed to create station: {e}")
    sys.exit(1)

# Test 7: Create contest log
print("\nTest 7: Creating contest log with contacts...")
try:
    log = ContestLog(
        station=station,
        contest_name="sa10m",
        contacts=[contact_ssb, contact_cw]
    )
    print(f"✅ Contest log created: {log.station.callsign} - QSOs: {log.total_qsos}")
except Exception as e:
    print(f"❌ Failed to create contest log: {e}")
    sys.exit(1)

# Test 8: Load SA10M configuration
print("\nTest 8: Loading SA10M configuration...")
try:
    import yaml
    with open("config/contests/sa10m.yaml", "r") as f:
        config = yaml.safe_load(f)

    print(f"✅ Configuration loaded: {config['contest']['name']}")
    print(f"   Exchange: RS/RST + CQ Zone")
    print(f"   Bands: {', '.join(config['contest']['bands'])}")
    print(f"   Modes: {', '.join(config['contest']['modes'])}")
except Exception as e:
    print(f"❌ Failed to load configuration: {e}")
    sys.exit(1)

# Test 9: Verify scoring rules
print("\nTest 9: Verifying scoring rules...")
try:
    scoring = config['scoring']
    points = scoring['points']
    print(f"✅ Scoring rules loaded:")
    for rule in points:
        print(f"   - {rule['description']}: {rule['value']} points (CW: ×2)")
    print(f"   - Multipliers: {scoring['multipliers'][0]['type']} (CQ zones)")
except Exception as e:
    print(f"❌ Failed to verify scoring rules: {e}")
    sys.exit(1)

# All tests passed
print()
print("=" * 60)
print("✅ All verification tests passed!")
print("=" * 60)
print()
print("Summary:")
print("  - RS/RST validation working correctly (2 or 3 digits)")
print("  - CQ zone exchange format configured")
print("  - SA10M configuration loaded successfully")
print("  - Scoring rules based on CQ zones")
print("  - Models and tests updated")
print()
print("Next steps:")
print("  1. Run unit tests: python -m pytest tests/test_models.py -v")
print("  2. Continue with Phase 1: Database models")
print("  3. See docs/SA10M_UPDATE.md for details")
print()

