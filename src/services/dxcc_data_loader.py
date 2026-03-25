"""
DXCC Data Loader Service

Loads and manages DXCC entity data from CTY.DAT file format.
Uses pyhamtools for callsign lookup and CTY.DAT parsing.

CTY.DAT Format Reference:
https://www.country-files.com/cty-dat-format/

Format:
  Line 1: Country Name:CQ Zone:ITU Zone:Continent:Latitude:Longitude:GMT Offset:Primary Prefix;
  Line 2+: Prefix variations (comma-separated), ending with semicolon

Example:
  Argentina:                 13:  14:  SA:   -34.00:    64.00:     3.0:  LU:
      =LU1AA,=LU1ZA,AY,AZ,L2,L3,L4,L5,L6,L7,L8,L9,LO,LP,LQ,LR,LT,LU,LW;
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from pyhamtools import LookupLib, Callinfo

from ..database.models import CTYData
from ..database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DXCCDataLoader:
    """Load and manage DXCC data from CTY.DAT file."""

    def __init__(self, cty_file_path: str = "cty_wt.dat", db_manager: Optional[DatabaseManager] = None):
        """
        Initialize DXCC data loader.

        Args:
            cty_file_path: Path to CTY.DAT file (default: cty_wt.dat in root)
            db_manager: Optional database manager instance
        """
        self.cty_file_path = Path(cty_file_path)
        self.db_manager = db_manager or DatabaseManager()
        self.lookup_lib = None

    def initialize_lookup_lib(self) -> bool:
        """
        Initialize pyhamtools LookupLib with CTY.DAT file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.cty_file_path.exists():
                logger.error(f"CTY.DAT file not found: {self.cty_file_path}")
                logger.info("Download from: https://www.country-files.com/cty/cty.dat")
                return False

            # Initialize lookup library with CTY.DAT
            self.lookup_lib = LookupLib(
                lookuptype="countryfile",
                filename=str(self.cty_file_path)
            )

            logger.info(f"✓ Initialized LookupLib with {self.cty_file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LookupLib: {e}")
            return False

    def lookup_callsign(self, callsign: str) -> Optional[Dict]:
        """
        Look up DXCC information for a callsign using pyhamtools.

        Args:
            callsign: Callsign to look up

        Returns:
            Dictionary with DXCC information or None if not found
        """
        if not self.lookup_lib:
            if not self.initialize_lookup_lib():
                return None

        try:
            callinfo = Callinfo(self.lookup_lib)
            info = callinfo.get_all(callsign)

            if not info:
                return None

            return {
                'callsign': callsign,
                'country': info.get('country'),
                'adif': info.get('adif'),  # DXCC entity code
                'continent': info.get('continent'),
                'cq_zone': info.get('cqz'),
                'itu_zone': info.get('ituz'),
                'latitude': info.get('latitude'),
                'longitude': info.get('longitude'),
                'prefix': info.get('prefix')
            }

        except Exception as e:
            logger.debug(f"Failed to lookup callsign {callsign}: {e}")
            return None

    def parse_cty_dat(self) -> List[Dict]:
        """
        Parse CTY.DAT file to extract all DXCC entities.

        CTY.DAT Format:
        # ADIF 246
        Country:CQ Zone:ITU Zone:Continent:Latitude:Longitude:GMT Offset:DXCC Prefix;
        prefix1,prefix2,prefix3;

        Returns:
            List of dictionaries with entity information
        """
        entities = []

        try:
            # Read file with multiple encoding attempts
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(self.cty_file_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    break
                except Exception:
                    continue

            if not content:
                logger.error("Failed to read CTY.DAT with any encoding")
                return []

            # Parse line by line to capture ADIF codes from comments
            lines_list = content.split('\n')
            
            # Process lines and extract ADIF codes
            processed_lines = []
            current_adif = None
            
            for line in lines_list:
                stripped = line.strip()
                # Check for ADIF code in comment
                if stripped.startswith('# ADIF'):
                    match = re.search(r'# ADIF (\d+)', stripped)
                    if match:
                        current_adif = int(match.group(1))
                elif not stripped.startswith('#') and stripped:
                    # Non-comment line - attach ADIF code if we have one
                    if current_adif and ':' in stripped:
                        # This is a country line, prepend ADIF marker
                        processed_lines.append(f"ADIF:{current_adif}:{stripped}")
                        current_adif = None  # Reset after using
                    else:
                        processed_lines.append(stripped)
            
            content = '\n'.join(processed_lines)

            # Split by semicolon (end of entity block)
            entity_blocks = content.split(';')

            for block in entity_blocks:
                if not block.strip():
                    continue

                lines = block.strip().split('\n')
                if not lines:
                    continue

                # First line contains main entity info
                main_line = lines[0].strip()
                if ':' not in main_line:
                    continue

                # Parse main line: ADIF:###:Country:CQ:ITU:Continent:Lat:Long:TZ:Prefix
                # OR Country:CQ:ITU:Continent:Lat:Long:TZ:Prefix (old format)
                parts = [p.strip() for p in main_line.split(':')]
                
                # Check if line starts with ADIF marker
                dxcc_code = 0
                offset = 0
                if parts[0] == 'ADIF' and len(parts) > 8:
                    dxcc_code = int(parts[1]) if parts[1] else 0
                    offset = 2  # Skip ADIF:### prefix
                
                if len(parts) < 8 + offset:
                    continue

                try:
                    country_name = parts[0 + offset]
                    cq_zone = int(parts[1 + offset]) if parts[1 + offset] else 0
                    itu_zone = int(parts[2 + offset]) if parts[2 + offset] else 0
                    continent = parts[3 + offset]
                    latitude = float(parts[4 + offset]) if parts[4 + offset] else 0.0
                    longitude = -float(parts[5 + offset]) if parts[5 + offset] else 0.0  # Western longitudes are positive in CTY.DAT
                    timezone_offset = float(parts[6 + offset]) if parts[6 + offset] else 0.0
                    primary_prefix = parts[7 + offset]

                    # Also check for old format ADIF code in country name (e.g., "Argentina (*100)")
                    if dxcc_code == 0:
                        dxcc_code = self._extract_dxcc_code(country_name)
                    # Remove DXCC code from country name if present
                    country_name = re.sub(r'\s*\(\*\d+\)\s*', '', country_name).strip()

                    # Parse prefix lines (lines 2+)
                    prefixes = self._parse_prefixes(lines[1:] if len(lines) > 1 else [])

                    # Add primary prefix if not in list
                    if primary_prefix and primary_prefix not in prefixes:
                        prefixes.insert(0, primary_prefix)

                    entity = {
                        'country_name': country_name,
                        'dxcc_code': dxcc_code,
                        'cq_zone': cq_zone,
                        'itu_zone': itu_zone,
                        'continent': continent,
                        'latitude': latitude,
                        'longitude': longitude,
                        'timezone_offset': timezone_offset,
                        'primary_prefix': primary_prefix,
                        'prefixes': prefixes
                    }
                    entities.append(entity)

                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse entity from line: {main_line[:50]}... ({e})")
                    continue

            logger.info(f"✓ Parsed {len(entities)} entities from CTY.DAT")
            return entities

        except Exception as e:
            logger.error(f"Failed to parse CTY.DAT: {e}")
            return []

    def _extract_dxcc_code(self, country_name: str) -> int:
        """
        Extract DXCC/ADIF code from country name.
        CTY.DAT includes (*###) for ADIF code in country name.

        Args:
            country_name: Country name potentially with ADIF code like "Argentina (*100)"

        Returns:
            ADIF code or 0 if not found
        """
        match = re.search(r'\(\*(\d+)\)', country_name)
        if match:
            return int(match.group(1))
        return 0

    def _parse_prefixes(self, prefix_lines: List[str]) -> List[str]:
        """
        Parse prefix lines from CTY.DAT entity block.
        Extracts all prefix variations, filtering out special modifiers.

        Args:
            prefix_lines: Lines containing comma-separated prefixes

        Returns:
            List of clean prefixes
        """
        prefixes = []

        # Join all prefix lines
        prefix_text = ' '.join(prefix_lines).strip()
        if not prefix_text:
            return prefixes

        # Split by comma
        prefix_parts = prefix_text.split(',')

        for part in prefix_parts:
            part = part.strip()
            if not part:
                continue

            # Remove special markers:
            # = exact callsign match
            # [##] CQ zone override
            # (#) ITU zone override
            # <##/##> lat/long override
            # {continent} continent override
            # ~##~ time zone override

            # Extract base prefix (remove markers)
            prefix = re.sub(r'[=\[\](){}<>~#]', '', part)
            prefix = prefix.strip()

            if prefix and prefix not in prefixes:
                prefixes.append(prefix)

        return prefixes

    def populate_database(self, session: Optional[Session] = None) -> Dict[str, int]:
        """
        Populate database with DXCC entities from CTY.DAT.

        Args:
            session: Optional existing database session

        Returns:
            Dictionary with statistics (added, updated, errors)
        """
        stats = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        # Parse CTY.DAT file
        entities = self.parse_cty_dat()

        if not entities:
            logger.error("No entities parsed from CTY.DAT")
            stats['errors'] = 1
            return stats

        # Get current timestamp for tracking
        file_date = datetime.fromtimestamp(self.cty_file_path.stat().st_mtime).strftime('%Y-%m-%d')

        try:
            # Use provided session or create new one
            if session:
                self._process_entities(session, entities, file_date, stats)
            else:
                with self.db_manager.get_session() as session:
                    self._process_entities(session, entities, file_date, stats)

            logger.info(f"✓ Database population complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to populate database: {e}", exc_info=True)
            stats['errors'] += 1
            return stats

    def _process_entities(self, session: Session, entities: List[Dict],
                         file_date: str, stats: Dict[str, int]) -> None:
        """Process and save entities to database."""

        for entity in entities:
            try:
                # Check if entity exists by DXCC code or primary prefix
                existing = None
                if entity['dxcc_code'] > 0:
                    existing = session.query(CTYData).filter_by(
                        dxcc_code=entity['dxcc_code']
                    ).first()

                if not existing and entity['primary_prefix']:
                    existing = session.query(CTYData).filter_by(
                        primary_prefix=entity['primary_prefix']
                    ).first()

                if existing:
                    # Update existing entity
                    existing.country_name = entity['country_name']
                    existing.dxcc_code = entity['dxcc_code'] if entity['dxcc_code'] > 0 else None
                    existing.continent = entity['continent']
                    existing.cq_zone = entity['cq_zone']
                    existing.itu_zone = entity['itu_zone']
                    existing.latitude = entity['latitude']
                    existing.longitude = entity['longitude']
                    existing.timezone_offset = entity['timezone_offset']
                    existing.primary_prefix = entity['primary_prefix']
                    existing.prefixes = entity['prefixes']
                    existing.last_updated = datetime.utcnow()
                    existing.cty_file_date = file_date
                    stats['updated'] += 1
                else:
                    # Add new entity
                    new_entity = CTYData(
                        country_name=entity['country_name'],
                        dxcc_code=entity['dxcc_code'] if entity['dxcc_code'] > 0 else None,
                        continent=entity['continent'],
                        cq_zone=entity['cq_zone'],
                        itu_zone=entity['itu_zone'],
                        latitude=entity['latitude'],
                        longitude=entity['longitude'],
                        timezone_offset=entity['timezone_offset'],
                        primary_prefix=entity['primary_prefix'],
                        prefixes=entity['prefixes'],
                        last_updated=datetime.utcnow(),
                        cty_file_date=file_date,
                        is_active=True
                    )
                    session.add(new_entity)
                    stats['added'] += 1

            except Exception as e:
                logger.error(f"Error processing entity {entity.get('country_name')}: {e}")
                stats['errors'] += 1

    def get_entity_by_callsign(self, callsign: str, session: Optional[Session] = None) -> Optional[CTYData]:
        """
        Get DXCC entity for a callsign by checking prefixes in database.

        Args:
            callsign: Callsign to lookup
            session: Optional database session

        Returns:
            CTYData entity or None
        """
        # First try pyhamtools lookup
        info = self.lookup_callsign(callsign)
        if info and info.get('adif'):
            if session:
                return session.query(CTYData).filter_by(dxcc_code=info['adif']).first()
            else:
                with self.db_manager.get_session() as session:
                    return session.query(CTYData).filter_by(dxcc_code=info['adif']).first()

        # Fallback: manual prefix matching from database
        # This is less accurate but can work without pyhamtools
        return None

    def update_from_file(self) -> Dict[str, int]:
        """
        Update database from CTY.DAT file.
        Convenience method that combines parsing and population.

        Returns:
            Statistics dictionary
        """
        logger.info(f"Updating DXCC data from {self.cty_file_path}")
        return self.populate_database()

