"""
Log Processing Pipeline

Complete pipeline for importing and validating contest logs:
1. Import Cabrillo files into database
2. Validate contacts (duplicates, exchange, callsigns, etc.)
3. Generate validation reports
"""

from typing import List, Dict, Optional
from pathlib import Path
import logging

from ..database.db_manager import DatabaseManager
from ..services.log_import_service import LogImportService
from ..core.validation import ContactValidator, BatchValidator
from ..core.rules.rules_loader import RulesLoader
from ..database.repositories import LogRepository, ContactRepository

logger = logging.getLogger(__name__)


class LogProcessingPipeline:
    """
    Complete pipeline for processing contest logs.

    Workflow:
    1. Import Cabrillo file(s) into database
    2. Validate all contacts
    3. Generate validation report
    """

    def __init__(self, db_manager: DatabaseManager, rules_file: str = None, contest_id: int = None):
        """
        Initialize the processing pipeline.

        Args:
            db_manager: Database manager instance
            rules_file: Path to contest rules YAML file
            contest_id: Contest ID for importing logs (optional, can be set per file)
        """
        self.db_manager = db_manager
        self.contest_id = contest_id

        # Ensure database tables exist
        try:
            db_manager.create_all_tables()
        except Exception as e:
            logger.warning(f"Error creating tables (may already exist): {e}")

        self.import_service = LogImportService(db_manager)

        # Load contest rules
        rules_loader = RulesLoader()
        if rules_file is None:
            self.rules = rules_loader.load_contest('sa10m')
        else:
            # Load from custom file path
            import yaml
            from pathlib import Path
            with open(rules_file, 'r') as f:
                rules_data = yaml.safe_load(f)
            from ..core.rules.rules_loader import ContestRules
            self.rules = ContestRules(**rules_data)

        logger.info(f"Pipeline initialized with rules: {self.rules.contest.name}")

    def process_file(self, file_path: str, contest_id: Optional[int] = None,
                    validate: bool = True) -> Dict[str, any]:
        """
        Process a single Cabrillo file: import and validate.

        Args:
            file_path: Path to the Cabrillo file
            contest_id: Contest ID (optional - uses pipeline contest_id if not provided)
            validate: Whether to run validation after import (default: True)

        Returns:
            Dictionary with processing results:
            {
                'import': {...},  # Import results
                'validation': {...},  # Validation results (if validate=True)
                'success': bool,
                'message': str
            }
        """
        result = {
            'success': False,
            'file': file_path,
            'import': None,
            'validation': None,
            'message': ''
        }

        try:
            # Use pipeline contest_id if none provided
            if contest_id is None:
                contest_id = self.contest_id

            if contest_id is None:
                result['message'] = "No contest_id provided"
                logger.error(result['message'])
                return result

            # Step 1: Import the log
            logger.info(f"Importing: {file_path}")
            import_result = self.import_service.import_cabrillo_file(file_path, contest_id)
            result['import'] = import_result

            if not import_result['success']:
                result['message'] = f"Import failed: {import_result['message']}"
                return result

            log_id = import_result['log_id']
            callsign = import_result['callsign']

            # Step 2: Validate (if requested)
            if validate:
                logger.info(f"Validating log {log_id} ({callsign})")

                with self.db_manager.get_session() as session:
                    contact_repo = ContactRepository(session)
                    validator = ContactValidator(contact_repo, self.rules)

                    # Get contest dates if available
                    log_repo = LogRepository(session)
                    db_log = log_repo.get_by_id(log_id)

                    contest_start = None
                    contest_end = None
                    if db_log and db_log.contest:
                        contest_start = db_log.contest.start_date
                        contest_end = db_log.contest.end_date

                    validation_result = validator.validate_log(
                        log_id,
                        contest_start,
                        contest_end
                    )

                    session.commit()

                result['validation'] = validation_result

                # Create summary message
                val = validation_result
                result['message'] = (
                    f"Successfully processed {callsign}: "
                    f"{val['total_contacts']} QSOs "
                    f"({val['valid_contacts']} valid, "
                    f"{val['duplicate_contacts']} duplicates, "
                    f"{val['invalid_contacts']} invalid)"
                )
                result['success'] = True
            else:
                result['message'] = f"Successfully imported {callsign}"
                result['success'] = True

        except Exception as e:
            result['message'] = f"Error processing file: {str(e)}"
            logger.error(result['message'], exc_info=True)

        return result

    def process_directory(self, directory_path: str, pattern: str = "*.txt",
                         contest_id: Optional[int] = None,
                         validate: bool = True) -> Dict[str, any]:
        """
        Process all Cabrillo files in a directory.

        Args:
            directory_path: Path to directory containing log files
            pattern: File pattern to match (default: *.txt)
            contest_id: Optional contest ID
            validate: Whether to run validation after import

        Returns:
            Dictionary with batch processing results
        """
        results = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'total_contacts': 0,
            'valid_contacts': 0,
            'duplicate_contacts': 0,
            'invalid_contacts': 0,
            'details': []
        }

        directory = Path(directory_path)
        if not directory.exists():
            results['message'] = f"Directory not found: {directory_path}"
            return results

        # Find all matching files
        files = list(directory.glob(pattern))
        results['total_files'] = len(files)

        logger.info(f"Processing {len(files)} files from {directory_path}")

        for file_path in files:
            logger.info(f"Processing {file_path.name}")
            result = self.process_file(str(file_path), contest_id, validate)

            if result['success']:
                results['successful'] += 1

                # Accumulate statistics
                if result['validation']:
                    val = result['validation']
                    results['total_contacts'] += val['total_contacts']
                    results['valid_contacts'] += val['valid_contacts']
                    results['duplicate_contacts'] += val['duplicate_contacts']
                    results['invalid_contacts'] += val['invalid_contacts']
            else:
                results['failed'] += 1

            results['details'].append({
                'file': file_path.name,
                'success': result['success'],
                'import': result.get('import'),
                'validation': result.get('validation'),
                'message': result['message']
            })

        results['message'] = (
            f"Processed {results['successful']}/{results['total_files']} files successfully. "
            f"Total: {results['total_contacts']} QSOs "
            f"({results['valid_contacts']} valid, "
            f"{results['duplicate_contacts']} duplicates, "
            f"{results['invalid_contacts']} invalid)"
        )

        logger.info(results['message'])

        return results

    def validate_existing_logs(self, log_ids: List[int] = None) -> Dict[str, any]:
        """
        Validate logs that are already in the database.

        Args:
            log_ids: List of log IDs to validate (if None, validates all logs)

        Returns:
            Validation summary
        """
        try:
            with self.db_manager.get_session() as session:
                contact_repo = ContactRepository(session)
                log_repo = LogRepository(session)

                # Get log IDs if not provided
                if log_ids is None:
                    all_logs = log_repo.get_all()
                    log_ids = [log.id for log in all_logs]

                if not log_ids:
                    return {
                        'success': False,
                        'message': 'No logs found to validate'
                    }

                logger.info(f"Validating {len(log_ids)} logs")

                # Validate each log
                batch_validator = BatchValidator(contact_repo, self.rules)

                # Get contest dates from first log
                first_log = log_repo.get_by_id(log_ids[0])
                contest_start = None
                contest_end = None
                if first_log and first_log.contest:
                    contest_start = first_log.contest.start_date
                    contest_end = first_log.contest.end_date

                results = batch_validator.validate_contest(
                    log_ids,
                    contest_start,
                    contest_end
                )

                session.commit()

                results['success'] = True
                results['message'] = (
                    f"Validated {results['total_logs']} logs: "
                    f"{results['total_contacts']} QSOs "
                    f"({results['valid_contacts']} valid, "
                    f"{results['duplicate_contacts']} duplicates, "
                    f"{results['invalid_contacts']} invalid)"
                )

                return results

        except Exception as e:
            logger.error(f"Error validating logs: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }


def process_cabrillo_files(file_or_directory: str, db_path: str = "sa10_contest.db",
                          rules_file: str = None, validate: bool = True) -> Dict[str, any]:
    """
    Convenience function to process Cabrillo file(s) with import and validation.

    Args:
        file_or_directory: Path to a single file or directory of files
        db_path: Path to database file
        rules_file: Path to contest rules YAML file
        validate: Whether to run validation after import

    Returns:
        Processing results
    """
    db_manager = DatabaseManager(db_path)
    pipeline = LogProcessingPipeline(db_manager, rules_file)

    path = Path(file_or_directory)

    if path.is_file():
        # Process single file
        return pipeline.process_file(str(path), validate=validate)
    elif path.is_dir():
        # Process directory
        return pipeline.process_directory(str(path), validate=validate)
    else:
        return {
            'success': False,
            'message': f"Path not found: {file_or_directory}"
        }

