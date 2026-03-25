"""
Update DXCC Reference Data from CTY.DAT File

This script updates the database with DXCC entity information from a CTY.DAT file.
The CTY.DAT file contains country/prefix data used for callsign lookup.

Usage:
    python update_dxcc_data.py
    python update_dxcc_data.py --cty-file cty.dat
    python update_dxcc_data.py --db-path data/ham_contest.db

Download CTY.DAT from:
    https://www.country-files.com/cty/cty.dat

Format Reference:
    https://www.country-files.com/cty-dat-format/
"""

import argparse
import logging
import sys
from pathlib import Path

from src.services.dxcc_data_loader import DXCCDataLoader
from src.database.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Update DXCC reference data from CTY.DAT file."""
    parser = argparse.ArgumentParser(
        description='Update DXCC data from CTY.DAT file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_dxcc_data.py
  python update_dxcc_data.py --cty-file cty.dat
  python update_dxcc_data.py --db-path sa10_contest.db
  
Download CTY.DAT:
  https://www.country-files.com/cty/cty.dat
        """
    )
    parser.add_argument(
        '--cty-file',
        default='cty_wt.dat',
        help='Path to CTY.DAT file (default: cty_wt.dat)'
    )
    parser.add_argument(
        '--db-path',
        default='sa10_contest.db',
        help='Path to database file (default: sa10_contest.db)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )

    args = parser.parse_args()

    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Verify CTY.DAT exists
    cty_path = Path(args.cty_file)
    if not cty_path.exists():
        logger.error(f"✗ CTY.DAT file not found: {cty_path}")
        logger.info("Download from: https://www.country-files.com/cty/cty.dat")
        return 1

    # Verify database exists
    db_path = Path(args.db_path)
    if not db_path.exists():
        logger.error(f"✗ Database file not found: {db_path}")
        logger.info("Create database first using import_logs.py or manage_contest.py")
        return 1

    logger.info("=" * 70)
    logger.info("DXCC Data Update")
    logger.info("=" * 70)
    logger.info(f"CTY.DAT file: {cty_path.absolute()}")
    logger.info(f"Database:     {db_path.absolute()}")
    logger.info("")

    # Initialize database and loader
    try:
        db_manager = DatabaseManager(str(db_path))
        loader = DXCCDataLoader(cty_file_path=str(cty_path), db_manager=db_manager)
    except Exception as e:
        logger.error(f"✗ Failed to initialize: {e}")
        return 1

    # Populate database
    logger.info("Parsing CTY.DAT file...")
    stats = loader.populate_database()

    # Print results
    logger.info("")
    logger.info("=" * 70)
    logger.info("DXCC Data Update Complete")
    logger.info("=" * 70)
    logger.info(f"  Entities added:   {stats['added']}")
    logger.info(f"  Entities updated: {stats['updated']}")
    logger.info(f"  Errors:           {stats['errors']}")
    logger.info("=" * 70)

    if stats['errors'] > 0:
        logger.warning(f"⚠ Completed with {stats['errors']} error(s)")
        return 1

    logger.info("✓ DXCC data successfully updated!")

    # Test lookup if pyhamtools is available
    try:
        logger.info("")
        logger.info("Testing callsign lookup...")
        test_calls = ['LU1HLH', 'W1AW', 'CE1KR', 'EA5BH', 'JA1ZZZ']

        for call in test_calls:
            info = loader.lookup_callsign(call)
            if info:
                logger.info(f"  {call:10s} → {info['country']:20s} (Zone: {info['cq_zone']}, {info['continent']})")
            else:
                logger.info(f"  {call:10s} → Not found")
    except Exception as e:
        logger.debug(f"Lookup test failed: {e}")

    return 0


if __name__ == '__main__':
    sys.exit(main())

