# DXCC Data Management Quick Start

## Overview

The DXCC (DX Century Club) data loader provides country and prefix information for ham radio callsigns using the CTY.DAT file format. This data is essential for:

- Identifying the country/DXCC entity of callsigns
- Determining CQ zones and ITU zones
- Calculating contest multipliers
- Validating log exchanges

## Quick Start

### Using the Desktop Application (recommended)

The desktop application includes a built-in DXCC data import that reads `cty_wt.dat` from the application folder — no separate download needed.

**First-time setup (new database)**

1. Create a new database via **File → New Database…**
2. DXCC data is loaded automatically into the new database.

**Refreshing an existing database**

1. Open the target database via **File → Open Database…**
2. Go to **File → Update DXCC Data…**
3. The import runs in the background; watch the output log for confirmation:
   ```
   DXCC data updated — 340 added, 0 updated, 0 errors.
   ```

> **Important:** DXCC data must be loaded before running scoring. Without it the continent/zone lookup returns empty values and all contacts score 0 points.

---

### Using the Command Line

#### 1. Download CTY.DAT File

```bash
# Download from country-files.com (recommended)
curl -O https://www.country-files.com/cty/cty.dat

# Or download manually from:
# https://www.country-files.com/cty/cty.dat
```

Place the `cty.dat` file in the project root directory.

#### 2. Update Database with CTY.DAT

```bash
# Update using default paths (cty_wt.dat and sa10_contest.db)
python update_dxcc_data.py

# Or specify custom paths
python update_dxcc_data.py --cty-file cty.dat --db-path sa10_contest.db

# Verbose output
python update_dxcc_data.py --verbose
```

#### 3. Expected Output

```
======================================================================
DXCC Data Update
======================================================================
CTY.DAT file: C:\Users\...\SA10\cty.dat
Database:     C:\Users\...\SA10\sa10_contest.db

Parsing CTY.DAT file...
✓ Parsed 340 entities from CTY.DAT
✓ Database population complete: {'added': 340, 'updated': 0, 'skipped': 0, 'errors': 0}

======================================================================
DXCC Data Update Complete
======================================================================
  Entities added:   340
  Entities updated: 0
  Errors:           0
======================================================================
✓ DXCC data successfully updated!

Testing callsign lookup...
  LU1HLH     → Argentina            (Zone: 13, SA)
  W1AW       → United States        (Zone: 5, NA)
  CE1KR      → Chile                (Zone: 12, SA)
  EA5BH      → Spain                (Zone: 14, EU)
  JA1ZZZ     → Japan                (Zone: 25, AS)
```

## CTY.DAT File Format

The CTY.DAT file uses the following format:

```
Country Name:CQ Zone:ITU Zone:Continent:Latitude:Longitude:GMT Offset:Primary Prefix;
  prefix1,prefix2,=exact_call,prefix3,...;
```

**Example:**
```
Argentina:                 13:  14:  SA:   -34.00:    64.00:     3.0:  LU:
  =LU1AA,=LU1ZA,AY,AZ,L2,L3,L4,L5,L6,L7,L8,L9,LO,LP,LQ,LR,LT,LU,LW;
```

### Special Markers in Prefixes

- `=` - Exact callsign match (e.g., =LU1AA)
- `[##]` - CQ zone override
- `(##)` - ITU zone override
- `<lat/long>` - Geographic coordinate override
- `{continent}` - Continent override
- `~##~` - Time zone override

## Usage in Code

### Using the DXCCDataLoader Service

```python
from src.services.dxcc_data_loader import DXCCDataLoader
from src.database.db_manager import DatabaseManager

# Initialize
db_manager = DatabaseManager('sa10_contest.db')
loader = DXCCDataLoader('cty_wt.dat', db_manager)

# Look up a callsign
info = loader.lookup_callsign('LU1HLH')
print(f"Country: {info['country']}")
print(f"CQ Zone: {info['cq_zone']}")
print(f"Continent: {info['continent']}")

# Update database from file
stats = loader.update_from_file()
print(f"Added: {stats['added']}, Updated: {stats['updated']}")
```

### Querying the Database

```python
from src.database.models import CTYData
from src.database.db_manager import DatabaseManager

db = DatabaseManager('sa10_contest.db')

with db.get_session() as session:
    # Get entity by DXCC code
    argentina = session.query(CTYData).filter_by(dxcc_code=100).first()
    print(f"{argentina.country_name}: {argentina.primary_prefix}")
    
    # Get all South American entities
    sa_entities = session.query(CTYData).filter_by(continent='SA').all()
    for entity in sa_entities:
        print(f"  {entity.primary_prefix}: {entity.country_name}")
    
    # Get entities in CQ Zone 13
    zone13 = session.query(CTYData).filter_by(cq_zone=13).all()
```

## Database Schema

The `cty_data` table stores:

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `country_name` | String | Country name (e.g., "Argentina") |
| `dxcc_code` | Integer | DXCC entity number |
| `continent` | String(2) | Continent code (SA, NA, EU, AS, AF, OC) |
| `itu_zone` | Integer | ITU zone number |
| `cq_zone` | Integer | CQ zone number (1-40) |
| `timezone_offset` | Float | UTC offset in hours |
| `latitude` | Float | Latitude |
| `longitude` | Float | Longitude |
| `primary_prefix` | String | Main prefix (e.g., "LU", "W", "JA") |
| `prefixes` | JSON | All prefix variations |
| `last_updated` | DateTime | Last update timestamp |
| `cty_file_date` | String | CTY.DAT file date |
| `is_active` | Boolean | Active status |

## Periodic Updates

CTY.DAT files are updated regularly as new DXCC entities are added or prefixes change.

### Update Schedule Recommendation

- **Before major contests**: Update 1-2 weeks before
- **Monthly**: For active scoring operations
- **Quarterly**: For historical analysis

### Update Process

Using the desktop application:

1. Open the database to update via **File → Open Database…**
2. Click **File → Update DXCC Data…** — the bundled `cty_wt.dat` is imported automatically.

Using the command line:

```bash
# 1. Download latest CTY.DAT
curl -O https://www.country-files.com/cty/cty.dat

# 2. Update database
python update_dxcc_data.py

# 3. Verify update
python update_dxcc_data.py --verbose
```

## Integration with Contest Scoring

The DXCC data is used during:

1. **Log Import** - Identify country/zone of each contact
2. **Validation** - Verify exchange data (zones, prefixes)
3. **Scoring** - Calculate points based on DXCC entities
4. **Multipliers** - Track unique prefixes and zones

### Example: Scoring Integration

```python
from src.services.dxcc_data_loader import DXCCDataLoader

class ScoringEngine:
    def __init__(self):
        self.dxcc_loader = DXCCDataLoader()
        self.dxcc_loader.initialize_lookup_lib()
    
    def calculate_points(self, my_call, their_call):
        """Calculate QSO points based on DXCC entities."""
        my_info = self.dxcc_loader.lookup_callsign(my_call)
        their_info = self.dxcc_loader.lookup_callsign(their_call)
        
        # SA10M scoring rules
        if my_info['continent'] == 'SA':
            if their_info['continent'] == 'SA':
                if my_info['adif'] != their_info['adif']:
                    return 2  # SA to SA, different country
                return 0  # Same country
            return 4  # SA to non-SA
        else:
            if their_info['continent'] == 'SA':
                return 4  # Non-SA to SA
            return 2  # Non-SA to non-SA
```

## Troubleshooting

### File Not Found

```
✗ CTY.DAT file not found: cty.dat
```

**Solution:** Download the file from https://www.country-files.com/cty/cty.dat

### Database Not Found

```
✗ Database file not found: sa10_contest.db
```

**Solution:** Create the database first using `manage_contest.py` or `import_logs.py`

### Encoding Issues

The loader tries multiple encodings (UTF-8, Latin-1, CP1252) automatically. If you still have issues, verify the file is a valid CTY.DAT format.

### Lookup Returns None

If callsign lookup returns `None`, it may be:
- Invalid callsign format
- New callsign not in CTY.DAT yet
- Special callsign (contest callsigns, special events)

## Additional Resources

- **CTY.DAT Format**: https://www.country-files.com/cty-dat-format/
- **Download CTY.DAT**: https://www.country-files.com/cty/cty.dat
- **DXCC Information**: http://www.arrl.org/dxcc
- **pyhamtools Documentation**: https://github.com/dh1tw/pyhamtools

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify CTY.DAT file is valid and up-to-date
3. Ensure database permissions are correct
4. Try verbose mode: `--verbose`

