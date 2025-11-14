# SA10M Contest - Quick Reference Card

## Scoring Rules Quick Reference

### Points Table

| Operator Type | Contact Type | Points | Rule |
|---------------|--------------|--------|------|
| **Mobile (/MM, /AM) in Zones 9-13** | | | |
| | → SA station | 2 | R3 |
| | → non-SA station | 4 | R4 |
| **Mobile (/MM, /AM) outside Zones 9-13** | | | |
| | → SA station | 4 | R5 |
| | → non-SA station | 2 | R6 |
| **Any station** | → Mobile station | 2 | R1 |
| **Any station** | → Same DXCC | 0 | R2 |
| **Non-SA station** | → SA station | 4 | R7 |
| **Non-SA station** | → non-SA station | 2 | R8 |
| **SA station** | → non-SA station | 4 | R9 |
| **SA station** | → SA station (diff DXCC) | 2 | R10 |

### Multipliers

| Type | Scope | Count | Description |
|------|-------|-------|-------------|
| **WPX Prefix** | Contest-wide | Once | Each unique prefix (e.g., LU1, LU2, W1) |
| **CQ Zone** | Per Band | Per band | Each zone worked (1-40) on each band |

### Score Formula

```
For each band:
  Band Score = QSO Points × (WPX Prefixes + CQ Zones on that band)

Total Score = Sum of all band scores
```

**Note**: SA10M is 10m only, so there's only one band.

### Exchange

**Send**: RS/RST + CQ Zone  
**Receive**: RS/RST + CQ Zone

- **SSB**: RS (2 digits) - e.g., "59"
- **CW**: RST (3 digits) - e.g., "599"
- **CQ Zone**: 1-40 (Argentina = Zone 13)

### Categories

- **SO-CW**: Single Operator CW only
- **SO-SSB**: Single Operator SSB only
- **SO-Mixed**: Single Operator CW + SSB
- **MO**: Multi Operator

### Contest Details

- **Band**: 10m only
- **Modes**: CW, SSB
- **Duration**: 24 hours
- **Duplicate Rule**: Same call on same band + mode = duplicate

### South American CQ Zones

| Zone | Coverage |
|------|----------|
| 9 | South America (northern) |
| 10 | South America (Venezuela, Guyana) |
| 11 | South America (Brazil north) |
| 12 | South America (Chile, Brazil south) |
| 13 | **Argentina** (primary) |

### Examples

#### Example 1: LU1ABC (Argentina, SA, Zone 13) operates

| Contact | Continent | DXCC | Points | Why |
|---------|-----------|------|--------|-----|
| PY2XYZ | SA | PY | 2 | SA→SA different DXCC (R10) |
| LU2DEF | SA | LU | 0 | Same DXCC (R2) |
| W1ABC | NA | K | 4 | SA→non-SA (R9) |
| DL1XYZ | EU | DL | 4 | SA→non-SA (R9) |
| LU3GHI/MM | SA | LU | 2 | Contact with mobile (R1) |

#### Example 2: W1ABC (USA, NA, Zone 5) operates

| Contact | Continent | DXCC | Points | Why |
|---------|-----------|------|--------|-----|
| LU1DEF | SA | LU | 4 | non-SA→SA (R7) |
| DL1XYZ | EU | DL | 2 | non-SA→non-SA (R8) |
| W2ABC | NA | K | 0 | Same DXCC (R2) |
| PY2GHI/MM | SA | PY | 2 | Contact with mobile (R1) |

#### Example 3: LU1ABC/MM (Mobile in Zone 13)

| Contact | Continent | Points | Why |
|---------|-----------|--------|-----|
| PY2XYZ | SA | 2 | Mobile in 9-13→SA (R3) |
| W1ABC | NA | 4 | Mobile in 9-13→non-SA (R4) |

#### Example 4: W1ABC/MM (Mobile in Zone 5)

| Contact | Continent | Points | Why |
|---------|-----------|--------|-----|
| LU1DEF | SA | 4 | Mobile outside 9-13→SA (R5) |
| DL1XYZ | EU | 2 | Mobile outside 9-13→non-SA (R6) |

### DXLog.net Mapping

Our YAML configuration exactly matches these DXLog parameters:

```
BANDS=10
MODES=CW;SSB
CATEGORY_MODES=CW;SSB;Mixed
DOUBLE_QSO=PER_MODE
MULT1_TYPE=WPX, MULT1_COUNT=ALL
MULT2_TYPE=CQZONE, MULT2_COUNT=PER_BAND
POINTS_TYPE=CALC
SCORE=BY_BAND
```

All 10 POINTS_FIELD_BAND_MODE rules are implemented in our YAML.

---

**Last Updated**: 2025-11-13  
**Configuration File**: `config/contests/sa10m.yaml`  
**Status**: ✅ Validated against DXLog.net definition

