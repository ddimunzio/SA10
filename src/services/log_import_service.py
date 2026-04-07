"""
Log Import Service

Combines parsing and database persistence for importing contest logs.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import logging
import os
from datetime import datetime

from ..parsers import parse_cabrillo_file
from ..database.db_manager import DatabaseManager
from ..database.repositories import LogRepository, ContactRepository
from ..database.models import Contest

logger = logging.getLogger(__name__)


class LogImportService:
    """
    Service for importing contest logs into the database.

    Handles the complete workflow:
    1. Parse Cabrillo file
    2. Create/find contest
    3. Save log (station) information
    4. Save all QSOs
    5. Return summary
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize log import service.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def import_cabrillo_file(self, file_path: str, contest_id: int) -> Dict[str, Any]:
        """
        Import a Cabrillo log file into the database.

        Args:
            file_path: Path to the Cabrillo file
            contest_id: Contest ID (required)

        Returns:
            Dictionary with import results:
            {
                'success': bool,
                'log_id': int,
                'callsign': str,
                'qso_count': int,
                'contest_id': int,
                'contest_name': str,
                'parse_errors': list,
                'parse_warnings': list,
                'message': str
            }
        """
        result = {
            'success': False,
            'log_id': None,
            'callsign': None,
            'qso_count': 0,
            'contest_id': None,
            'contest_name': None,
            'is_replacement': False,
            'parse_errors': [],
            'parse_warnings': [],
            'message': ''
        }

        try:
            # Step 1: Parse the Cabrillo file
            logger.info(f"Parsing Cabrillo file: {file_path}")
            parsed_log = parse_cabrillo_file(file_path, strict_mode=False)

            result['callsign'] = parsed_log.callsign
            result['parse_errors'] = parsed_log.parse_errors
            result['parse_warnings'] = parsed_log.parse_warnings

            # Check for critical parse errors
            if parsed_log.parse_errors:
                result['message'] = f"Parse errors: {'; '.join(parsed_log.parse_errors[:3])}"
                logger.error(result['message'])
                return result

            # Get file modification time
            file_modified_at = datetime.fromtimestamp(os.path.getmtime(file_path))

            # Step 2: Get or create session
            with self.db_manager.get_session() as session:
                log_repo = LogRepository(session)
                contact_repo = ContactRepository(session)

                # Step 3: Verify contest exists
                contest = session.query(Contest).filter(Contest.id == contest_id).first()
                if not contest:
                    result['message'] = f"Contest ID {contest_id} not found"
                    logger.error(result['message'])
                    return result

                result['contest_id'] = contest_id
                result['contest_name'] = contest.name

                # Step 4: Check if log already exists and handle versioning
                existing_log = log_repo.get_by_callsign(parsed_log.callsign, contest_id)
                is_replacement = False

                if existing_log:
                    # Check if this is a newer version of the file
                    if existing_log.file_modified_at and file_modified_at <= existing_log.file_modified_at:
                        logger.info(f"Skipping {parsed_log.callsign}: existing file is same or newer "
                                  f"(existing: {existing_log.file_modified_at}, new: {file_modified_at})")
                        result['message'] = f"Skipped: existing log is same or newer version"
                        result['log_id'] = existing_log.id
                        result['success'] = False
                        return result

                    # This is a newer version - delete the old log and its contacts
                    logger.info(f"Replacing existing log for {parsed_log.callsign} with newer version "
                              f"(old: {existing_log.file_modified_at}, new: {file_modified_at})")
                    log_repo.delete(existing_log.id)
                    is_replacement = True
                    result['is_replacement'] = True

                # Step 5: Create log entry
                logger.info(f"{'Replacing' if is_replacement else 'Creating'} log entry for {parsed_log.callsign}")
                db_log = log_repo.create(parsed_log, contest_id)

                # Set file metadata
                db_log.file_path = file_path
                db_log.file_modified_at = file_modified_at

                result['log_id'] = db_log.id

                # Step 6: Save all QSOs in batch
                if parsed_log.qsos:
                    logger.info(f"Saving {len(parsed_log.qsos)} QSOs")
                    contact_repo.create_batch(parsed_log.qsos, db_log.id)
                    result['qso_count'] = len(parsed_log.qsos)

                # Step 7: Mark log as validated and commit
                from src.database.models import ContestStatus
                db_log.status = ContestStatus.VALIDATED
                db_log.processed_at = __import__('datetime').datetime.utcnow()
                session.commit()

                result['success'] = True
                action = "Replaced" if is_replacement else "Successfully imported"
                result['message'] = f"{action} {result['qso_count']} QSOs for {parsed_log.callsign}"
                logger.info(result['message'])

        except FileNotFoundError as e:
            result['message'] = f"File not found: {file_path}"
            logger.error(result['message'])
        except Exception as e:
            result['message'] = f"Error importing log: {str(e)}"
            logger.error(result['message'], exc_info=True)

        return result

    def import_directory(self, directory_path: str, contest_id: int,
                        pattern: str = "*.txt") -> Dict[str, Any]:
        """
        Import all Cabrillo files from a directory.

        Args:
            directory_path: Path to directory containing log files
            contest_id: Contest ID (required)
            pattern: File pattern to match (default: *.txt)

        Returns:
            Dictionary with batch import results
        """
        results = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        directory = Path(directory_path)
        if not directory.exists():
            results['message'] = f"Directory not found: {directory_path}"
            return results

        # Find all matching files
        files = list(directory.glob(pattern))
        results['total_files'] = len(files)

        logger.info(f"Found {len(files)} files in {directory_path}")

        for file_path in files:
            logger.info(f"Processing {file_path.name}")
            result = self.import_cabrillo_file(str(file_path), contest_id)

            if result['success']:
                results['successful'] += 1
            elif 'Skipped' in result['message'] or 'already exists' in result['message']:
                results['skipped'] += 1
            else:
                results['failed'] += 1

            results['details'].append({
                'file': file_path.name,
                'callsign': result['callsign'],
                'success': result['success'],
                'qso_count': result['qso_count'],
                'message': result['message']
            })

        results['message'] = (
            f"Imported {results['successful']} logs, "
            f"skipped {results['skipped']}, "
            f"failed {results['failed']}"
        )
        logger.info(results['message'])

        return results



def import_cabrillo_to_db(file_path: str, contest_id: int, db_path: str = "sa10.db") -> Dict[str, Any]:
    """
    Convenience function to import a Cabrillo file to database.

    Args:
        file_path: Path to Cabrillo file
        contest_id: Contest ID (required)
        db_path: Path to database file (default: sa10.db)

    Returns:
        Import result dictionary
    """
    db_manager = DatabaseManager(db_path)
    db_manager.create_all_tables()

    service = LogImportService(db_manager)
    return service.import_cabrillo_file(file_path, contest_id)


def import_directory_to_db(directory_path: str, contest_id: int, db_path: str = "sa10.db",
                          pattern: str = "*.txt") -> Dict[str, Any]:
    """
    Convenience function to import all logs from a directory.

    Args:
        directory_path: Path to directory with log files
        contest_id: Contest ID (required)
        db_path: Path to database file (default: sa10.db)
        pattern: File pattern (default: *.txt)

    Returns:
        Batch import result dictionary
    """
    db_manager = DatabaseManager(db_path)
    db_manager.create_all_tables()

    service = LogImportService(db_manager)
    return service.import_directory(directory_path, contest_id, pattern)

