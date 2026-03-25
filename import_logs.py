#!/usr/bin/env python3
"""
Import Contest Logs Script

Usage:
    # First, create a contest (do this once):
    python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"

    # Import directory with contest ID:
    python import_logs.py --contest-id 1 --clean logs_sa10m_2025/

    # Import single file:
    python import_logs.py --contest-id 1 path/to/file.cbr

    # Import without validation:
    python import_logs.py --contest-id 1 --no-validate logs_sa10m_2025/

    # Or use the automated script:
    python import_all.py
"""

import sys
import argparse
from pathlib import Path

from src.database.db_manager import DatabaseManager
from src.services.log_processing_pipeline import LogProcessingPipeline
from src.utils import setup_logger


def main():
    parser = argparse.ArgumentParser(
        description='Import and validate contest logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'path',
        help='Path to Cabrillo file or directory of files'
    )

    parser.add_argument(
        '--contest-id',
        type=int,
        required=True,
        help='Contest ID (required - use manage_contest.py to create contests)'
    )

    parser.add_argument(
        '--db',
        default='sa10_contest.db',
        help='Database file path (default: sa10_contest.db)'
    )

    parser.add_argument(
        '--rules',
        help='Path to contest rules YAML file (default: built-in SA10M rules)'
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clear database before importing'
    )

    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip validation after import'
    )

    parser.add_argument(
        '--pattern',
        default='*.txt',
        help='File pattern for directory import (default: *.txt)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger("import_logs", console=True, level='DEBUG' if args.verbose else 'INFO')

    print("=" * 70)
    print("SA10M CONTEST LOG IMPORTER")
    print("=" * 70)
    print()

    # Initialize database
    db_manager = DatabaseManager(args.db)

    # Clean database if requested
    if args.clean:
        print("[*] Cleaning database...")
        logger.info(f"Resetting database: {args.db}")
        try:
            db_manager.reset_database()
            print("[OK] Database cleaned successfully\n")
        except Exception as e:
            print(f"[ERROR] Failed to clean database: {e}")
            logger.error(f"Database reset failed: {e}", exc_info=True)
            return 1

    # Initialize pipeline
    try:
        pipeline = LogProcessingPipeline(db_manager, args.rules, contest_id=args.contest_id)
    except Exception as e:
        print(f"[ERROR] Error initializing pipeline: {e}")
        logger.error(f"Pipeline initialization failed: {e}", exc_info=True)
        return 1

    # Process files
    path = Path(args.path)
    validate = not args.no_validate

    print(f"[>] Contest ID: {args.contest_id}")
    print(f"[>] Source: {path}")
    print(f"[>] Database: {args.db}")
    print(f"[>] Validation: {'enabled' if validate else 'disabled'}")
    print()

    if path.is_file():
        print(f"Processing file: {path.name}")
        print("-" * 70)
        result = pipeline.process_file(str(path), validate=validate)

        if result['success']:
            print(f"\n[OK] {result['message']}")

            if result.get('validation'):
                val = result['validation']
                print(f"\nValidation Summary:")
                print(f"  Total QSOs: {val['total_contacts']}")
                print(f"  Valid: {val['valid_contacts']}")
                print(f"  Duplicates: {val['duplicate_contacts']}")
                print(f"  Invalid: {val['invalid_contacts']}")

                if val.get('errors'):
                    print(f"\n[!] Validation Errors:")
                    for error in val['errors'][:10]:  # Show first 10 errors
                        print(f"    - {error}")
                    if len(val['errors']) > 10:
                        print(f"    ... and {len(val['errors']) - 10} more")
        else:
            print(f"\n[ERROR] {result['message']}")
            return 1

    elif path.is_dir():
        print(f"Processing directory: {path}")
        print(f"Pattern: {args.pattern}")
        print("-" * 70)
        result = pipeline.process_directory(str(path), pattern=args.pattern, validate=validate)

        print(f"\n{result['message']}")
        print(f"\nBatch Summary:")
        print(f"  Files processed: {result['successful']}/{result['total_files']}")
        print(f"  Total QSOs: {result['total_contacts']}")
        print(f"  Valid: {result['valid_contacts']}")
        print(f"  Duplicates: {result['duplicate_contacts']}")
        print(f"  Invalid: {result['invalid_contacts']}")

        if result['failed'] > 0:
            print(f"\n[!] Failed files: {result['failed']}")
            for detail in result['details']:
                if not detail['success']:
                    print(f"    - {detail['file']}: {detail['message']}")

    else:
        print(f"[ERROR] Path not found: {path}")
        return 1

    print()
    print("=" * 70)
    print("[OK] Import complete")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())

