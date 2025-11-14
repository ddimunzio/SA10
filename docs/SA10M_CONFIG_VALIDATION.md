# SA10M Contest Configuration Validation

This document compares the DXLog.net contest definition with our YAML configuration to ensure accuracy.

## DXLog.net vs Our Configuration

### ✅ MATCHES

#### 1. **Contest Basics**
- **Name**: South America 10m Contest ✓
- **Bands**: 10m only ✓
- **Modes**: CW, SSB ✓
- **Website**: http://sa10m.com.ar ✓

#### 2. **Categories**
- **DXLog**: Single operator, Multi-operator with CW/SSB/Mixed modes
- **Our Config**: 
  - Single Operator CW (SO-CW)
  - Single Operator SSB (SO-SSB)
  - Single Operator Mixed (SO-Mixed)
  - Multi Operator (MO)
- **Status**: ✓ Correct

#### 3. **Duplicate Rule**
- **DXLog**: `DOUBLE_QSO=PER_MODE` (same call on same band+mode is dupe)
- **Our Config**: `duplicate_window: type: "band_mode"`
- **Status**: ✓ Correct

#### 4. **Multipliers**

##### Multiplier 1: WPX Prefix
- **DXLog**: `MULT1_TYPE=WPX`, `MULT1_COUNT=ALL` (contest-wide)
- **Our Config**: `wpx_prefix`, `scope: "contest"`
- **Status**: ✓ Correct

##### Multiplier 2: CQ Zone
- **DXLog**: `MULT2_TYPE=CQZONE`, `MULT2_COUNT=PER_BAND`
- **Our Config**: `cq_zone`, `scope: "per_band"`
- **Status**: ✓ Correct

#### 5. **Scoring Rules**

Our configuration now correctly implements all 9 scoring rules from DXLog:

| Rule | Description | Points | DXLog Line | Our Config |
|------|-------------|--------|------------|------------|
| 1 | Contact with mobile station (/MM, /AM) | 2 | `DEST->CALL:/[AM]M$` | ✓ |
| 2 | Same DXCC entity | 0 | `SOURCE->DXCC:DEST->DXCC` | ✓ |
| 3 | Mobile in zones 9-13, SA contact | 2 | `CONFIG->CALL:/[AM]M$;CONFIG->CQZONE:^(09\|1[0123])$;...;DEST->CONT:^SA$` | ✓ |
| 4 | Mobile in zones 9-13, non-SA contact | 4 | `CONFIG->CALL:/[AM]M$;CONFIG->CQZONE:^(09\|1[0123])$;...;!DEST->CONT:^SA$` | ✓ |
| 5 | Mobile outside zones 9-13, SA contact | 4 | `CONFIG->CALL:/[AM]M$;!CONFIG->CQZONE:^(09\|1[0123])$;...;DEST->CONT:^SA$` | ✓ |
| 6 | Mobile outside zones 9-13, non-SA contact | 2 | `CONFIG->CALL:/[AM]M$;!CONFIG->CQZONE:^(09\|1[0123])$;...;!DEST->CONT:^SA$` | ✓ |
| 7 | Non-SA station contacts SA station | 4 | `!SOURCE->CONT:^SA$;DEST->CONT:^SA$` | ✓ |
| 8 | Non-SA station contacts non-SA station | 2 | `!SOURCE->CONT:^SA$;ALL;ALL;ALL` | ✓ |
| 9 | SA station contacts non-SA station | 4 | `SOURCE->CONT:^SA$;!DEST->CONT:^SA$` | ✓ |
| 10 | SA station contacts SA station | 2 | `SOURCE->CONT:^SA$;ALL;ALL;ALL` | ✓ |

**Note**: The order matters! Rules are evaluated top-to-bottom, first match wins.

#### 6. **Score Calculation**
- **DXLog**: `SCORE=BY_BAND` - Score calculated per band
- **Our Config**: `formula: "sum(band_points * (wpx_multipliers + zone_multipliers_per_band))"`
- **Status**: ✓ Correct - This matches the BY_BAND scoring where each band's QSO points are multiplied by the sum of multipliers for that band

### 📋 Exchange Format

#### Sent/Received
- **RS/RST**: Signal report (RS for SSB, RST for CW)
- **CQ Zone**: 1-40

**Status**: ✓ Correct

### 🔍 Key Insights from DXLog Definition

1. **Mobile stations are special**: They have different point values based on their CQ zone location
2. **Priority order**: Rules are checked in specific order (mobile first, then DXCC, then continent-based)
3. **Zone geography**: Zones 9-13 cover most of South America
4. **Multiplier counting**: 
   - WPX prefixes count ONCE for entire contest
   - CQ Zones count PER BAND (same zone on different bands = 2 mults)

### 🎯 Score Formula Breakdown

For each band:
```
Band Score = QSO Points × (WPX Prefix Count + CQ Zone Count for that band)
```

Total Score = Sum of all band scores

**Example**:
- Band: 10m
- QSOs: 100 contacts = 300 points
- WPX Prefixes worked: 50 (counted once across all modes)
- CQ Zones worked on 10m: 20
- Band Score: 300 × (50 + 20) = 21,000

### 📝 Changes Made

1. ✅ Fixed categories - changed "SOAB" to "SO-Mixed"
2. ✅ Completely rewrote scoring rules to match continent-based system
3. ✅ Added WPX prefix multiplier (was missing!)
4. ✅ Changed CQ zone multiplier from "contest" scope to "per_band"
5. ✅ Updated final score formula to match BY_BAND calculation
6. ✅ Added reference data for continents and mobile suffixes

### ✨ Configuration is Now Correct!

Your sa10m.yaml configuration now accurately reflects the official SA10M contest rules as defined in the DXLog.net contest file.

