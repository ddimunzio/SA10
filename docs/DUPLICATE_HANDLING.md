# Duplicate Contact Handling in SA10M Contest System

**Last Updated**: November 17, 2025

## Overview

The contest system handles duplicate contacts using a **two-phase approach**:

1. **Phase 5.1 (Import)**: Import ALL contacts without filtering — ✅ Complete
2. **Phase 4.1 (Scoring)**: Detect and exclude duplicates during scoring — ✅ Complete

This approach ensures complete data preservation and allows flexible duplicate detection based on contest-specific rules.

---

## Phase 5.1: Import Phase (CURRENT - COMPLETE ✅)

### What Happens During Import

When a Cabrillo log is imported via `LogImportService`:

1. **ALL contacts are imported** from the Cabrillo file
2. Every contact is saved to the database with:
   - `is_duplicate = False` (default)
   - `is_valid = True` (default)
   - `validation_status = 'valid'` (default)
3. **NO duplicate checking** or filtering occurs

### Why This Approach?

**Benefits:**
- ✅ **Data Integrity**: Complete log preservation as submitted
- ✅ **Audit Trail**: All contacts available for review
- ✅ **Flexibility**: Different contests can have different duplicate rules
- ✅ **Cross-checking**: Can verify if a duplicate was also logged by the other station
- ✅ **Scoring Control**: Duplicate detection happens during scoring with full contest context

### Example

If a log contains:
```
QSO: 28500 PH 2025-03-08 1200 TEST1ABC 59 13 W1AW 59 05
QSO: 28500 PH 2025-03-08 1210 TEST1ABC 59 13 W1AW 59 05  <- Duplicate
QSO: 28500 PH 2025-03-08 1220 TEST1ABC 59 13 W1AW 59 05  <- Duplicate
```

**All 3 contacts are imported** into the database with `is_duplicate=False`.

### Code Implementation

**ContactRepository.create_batch()** - No duplicate checking:
```python
def create_batch(self, contacts_data: List[ContactBase], log_id: int) -> List[DBContact]:
    """Create multiple contacts in batch for better performance."""
    db_contacts = []
    
    for contact_data in contacts_data:
        db_contact = DBContact(
            log_id=log_id,
            # ... other fields ...
            is_valid=True,
            is_duplicate=False,  # Default - will be updated in Phase 4.1
            validation_status='valid',
        )
        db_contacts.append(db_contact)
    
    self.session.add_all(db_contacts)
    self.session.flush()
    return db_contacts
```

### Verification

Run `test_duplicate_import.py` to verify:
```bash
python test_duplicate_import.py
```

Expected output:
```
✅ SUCCESS: Duplicate contacts are imported without being filtered!
   They will be processed during the scoring/validation phase.
```

---

## Phase 4.1: Scoring Phase (COMPLETE ✅)

Duplicate detection runs inside the **Scoring Engine** when processing each log. The scorer identifies duplicates (same callsign + same band + same mode), excludes them from point calculation, and stores the count in the `scores` table as `duplicate_qsos`. The result is visible in the **Leaderboard** tab under the **Dupes** column.

### Duplicate Rules

Different contests may have different duplicate windows:

**SA10M Contest:**
- **Rule**: Duplicate = same callsign + same band + same mode
- **Window**: Per band per mode (can work same station on CW and SSB)
- **Scoring**: First QSO counts, duplicates score 0 points

| Case | Duplicate? |
|------|-----------|
| Same callsign + same band + same mode | ✅ Yes (0 pts) |
| Same callsign + **different mode** (CW vs SSB) | ❌ No (valid QSO) |
| Same callsign + **different band** | ❌ No (valid QSO) |

**Other Contests (Future):**
- Some contests: Duplicate only on same band (mode doesn't matter)
- Some contests: Can work same station again after X hours
- Some contests: Different duplicate rules for different categories

#### Real Example: N6AR worked AY7J twice

In the SA10M 2026 log submitted by N6AR, AY7J appears twice:

```
QSO:   28040 CW 2026-03-14 2013 N6AR       599  05 AY7J          599  13         AY7
QSO:   28480 PH 2026-03-14 2034 N6AR       59   05 AY7J          59   13         AY7
```

- First QSO: **28 MHz CW** at 2013z
- Second QSO: **28 MHz PH (SSB)** at 2034z

These are **not duplicates** because the mode is different (CW ≠ PH). Both QSOs are valid and score points for N6AR.

> **Note on UBN reports**: The AY7J UBN report lists N6AR under *"Stations Copying AY7J Exchange Incorrectly"* because N6AR logged the exchange field as `AY7` (the callsign prefix) instead of `13` (the CQ zone). However, **AY7J does not lose credit** — it is N6AR who has the copying error.

### Implementation (To Be Done)

Will create `src/core/validation/contact_validator.py`:

```python
class ContactValidator:
    """Validate contacts and mark duplicates"""
    
    def validate_log(self, log_id: int, contest_rules: ContestRules):
        """Validate all contacts in a log"""
        
        # Get all contacts
        contacts = self.contact_repo.get_all_for_log(log_id)
        
        # Sort by timestamp
        contacts.sort(key=lambda c: c.qso_datetime)
        
        # Track what we've worked
        worked = set()  # (callsign, band, mode)
        
        for contact in contacts:
            key = (contact.call_received, contact.band, contact.mode)
            
            if key in worked:
                # Duplicate!
                self.contact_repo.mark_as_duplicate(contact.id)
            else:
                # First time working this station
                worked.add(key)
                
                # Additional validations:
                # - Check exchange format
                # - Check callsign validity
                # - Check time within contest
                # - etc.
```

### Database Support

The `Contact` model already has everything needed:

```python
class Contact(Base):
    # ... other fields ...
    
    # Validation fields
    is_duplicate = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True)
    validation_status = Column(String(50))  # 'valid', 'duplicate', 'invalid', etc.
    validation_message = Column(Text)
    
    # Indexed for fast duplicate queries
    Index("idx_contact_duplicate", "is_duplicate")
```

The `ContactRepository` already has the method:

```python
def mark_as_duplicate(self, contact_id: int) -> DBContact:
    """Mark a contact as duplicate"""
    db_contact = self.get_by_id(contact_id)
    if db_contact:
        db_contact.is_duplicate = True
        db_contact.validation_status = 'duplicate'
        db_contact.points = 0
        self.session.flush()
    return db_contact
```

---

## Scoring Integration

### Phase 4.2: Scoring Engine

When calculating scores, the engine will:

1. **Exclude duplicates** from scoring:
   ```python
   valid_contacts = [c for c in contacts if not c.is_duplicate and c.is_valid]
   ```

2. **Generate reports** showing:
   - Total QSOs logged
   - Valid QSOs (scored)
   - Duplicate QSOs (0 points)
   - Invalid QSOs (0 points)

3. **Detailed breakdown**:
   ```
   Total QSOs:      150
   Valid QSOs:      145
   Duplicate QSOs:    3  (0 points)
   Invalid QSOs:      2  (0 points)
   ```

### Rules Engine Integration

The `RulesEngine` (already implemented) will skip duplicates:

```python
def calculate_score(self, contacts: List[Contact]) -> ScoreBreakdown:
    """Calculate total score"""
    
    # Count valid vs duplicate
    valid_qsos = sum(1 for c in contacts if not c.is_duplicate)
    duplicate_qsos = sum(1 for c in contacts if c.is_duplicate)
    
    # Calculate points only for valid contacts
    for band in bands:
        band_contacts = [c for c in contacts 
                        if c.band == band and not c.is_duplicate]
        # ... calculate points and multipliers ...
```

---

## Benefits of This Two-Phase Approach

### Data Integrity
✅ Complete log preservation  
✅ Can review what was actually submitted  
✅ Audit trail for adjudication

### Flexibility
✅ Different duplicate rules per contest  
✅ Can re-validate with different rules  
✅ Can detect patterns (same station worked many times)

### Cross-Checking
✅ Can verify if duplicate was logged by other station  
✅ Can detect timing discrepancies  
✅ Better NIL (Not In Log) detection

### Performance
✅ Fast batch import (no duplicate queries)  
✅ Duplicate detection done once after import  
✅ Indexed database fields for fast queries

---

## Current Status

| Phase | Status | Description |
|-------|--------|-------------|
| 5.1 Import | ✅ Complete | All contacts imported without filtering |
| 4.1 Scoring | ✅ Complete | Duplicates detected and excluded by the scoring engine |
| 4.2 Leaderboard | ✅ Complete | Duplicate count displayed in the Dupes column |

---

## Testing

### Test Files

1. **`test_duplicate_import.py`** ✅
   - Verifies duplicates ARE imported
   - Confirms no filtering during import

2. **`tests/test_scoring_with_duplicates.py`** ✅
   - Verifies duplicates score 0 points
   - Tests final score calculation

### Manual Testing

Import a real log with duplicates:
```bash
python demo_import_logs.py logs_sa10m_2025/TEST_LOG.txt
```

Then query the database:
```python
from src.database.db_manager import DatabaseManager
from src.database.repositories import ContactRepository

db = DatabaseManager("sa10_contest.db")
with db.get_session() as session:
    repo = ContactRepository(session)
    contacts = repo.get_all_for_log(log_id=1)
    
    # All contacts should be imported
    print(f"Total contacts: {len(contacts)}")
    
    # None should be marked as duplicate yet
    dups = sum(1 for c in contacts if c.is_duplicate)
    print(f"Marked as duplicate: {dups}")  # Should be 0
```

---

## References

- **Database Schema**: `docs/DATABASE_SCHEMA.md`
- **Rules Engine**: `docs/RULES_ENGINE_QUICK_REF.md`
- **SA10M Rules**: `config/contests/sa10m.yaml`

---

**Document Version**: 1.0  
**Created**: November 17, 2025  
**Status**: Import phase complete, validation phase pending

