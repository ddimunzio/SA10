"""
Contact Validation Module

Validates contest contacts (QSOs) including:
- Duplicate detection
- Exchange format validation
- Callsign format validation
- Time validation (within contest period)
- Band and mode validation
"""

from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime
import re
import logging

from ..rules.rules_loader import ContestRules
from ...database.repositories import ContactRepository
from ...database.models import Contact
from ...utils import extract_cq_zone

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of validating a single contact"""

    def __init__(self, contact_id: int):
        self.contact_id = contact_id
        self.is_valid = True
        self.is_duplicate = False
        self.validation_status = 'valid'
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, error: str):
        """Add a validation error"""
        self.errors.append(error)
        self.is_valid = False
        self.validation_status = 'invalid'

    def add_warning(self, warning: str):
        """Add a validation warning"""
        self.warnings.append(warning)

    def mark_duplicate(self):
        """Mark this contact as a duplicate"""
        self.is_duplicate = True
        self.is_valid = False
        self.validation_status = 'duplicate'
        self.errors.append("Duplicate contact (same callsign/band/mode)")

    def get_message(self) -> str:
        """Get combined validation message"""
        messages = []
        if self.errors:
            messages.append(f"Errors: {'; '.join(self.errors)}")
        if self.warnings:
            messages.append(f"Warnings: {'; '.join(self.warnings)}")
        return ' | '.join(messages) if messages else None


class ContactValidator:
    """
    Validates contest contacts according to rules.

    Handles:
    - Duplicate detection (same callsign + band + mode)
    - Exchange format validation (RS/RST, CQ zone)
    - Callsign format validation
    - Time validation (within contest period)
    - Band and mode validation
    """

    def __init__(self, contact_repo: ContactRepository, rules: ContestRules):
        """
        Initialize the contact validator.

        Args:
            contact_repo: Repository for contact database operations
            rules: Contest rules for validation
        """
        self.contact_repo = contact_repo
        self.rules = rules

    def validate_log(self, log_id: int, contest_start: datetime = None,
                    contest_end: datetime = None) -> Dict[str, any]:
        """
        Validate all contacts in a log.

        Args:
            log_id: ID of the log to validate
            contest_start: Contest start datetime (optional)
            contest_end: Contest end datetime (optional)

        Returns:
            Dictionary with validation summary:
            {
                'total_contacts': int,
                'valid_contacts': int,
                'duplicate_contacts': int,
                'invalid_contacts': int,
                'errors': list of error messages,
                'warnings': list of warning messages
            }
        """
        logger.info(f"Starting validation for log {log_id}")

        # Get all contacts sorted by timestamp
        contacts = self.contact_repo.get_all_for_log(log_id)
        if not contacts:
            logger.warning(f"No contacts found for log {log_id}")
            return {
                'total_contacts': 0,
                'valid_contacts': 0,
                'duplicate_contacts': 0,
                'invalid_contacts': 0,
                'errors': [],
                'warnings': ['No contacts found in log']
            }

        # Sort by timestamp
        contacts.sort(key=lambda c: c.qso_datetime)

        # Track worked stations for duplicate detection
        worked: Set[Tuple[str, str, str]] = set()  # (callsign, band, mode)

        # Validation results
        results = []
        all_errors = []
        all_warnings = []

        for contact in contacts:
            result = ValidationResult(contact.id)

            # 1. Duplicate detection
            contact_key = (
                contact.call_received.upper(),
                contact.band,
                contact.mode
            )

            if contact_key in worked:
                result.mark_duplicate()
                logger.debug(f"Duplicate contact: {contact.call_received} on {contact.band} {contact.mode}")
            else:
                worked.add(contact_key)

            # Only do other validations if not duplicate
            if not result.is_duplicate:
                # 2. Exchange format validation
                self._validate_exchange(contact, result)

                # 3. Callsign format validation
                self._validate_callsign(contact, result)

                # 4. Time validation
                if contest_start and contest_end:
                    self._validate_time(contact, contest_start, contest_end, result)

                # 5. Band validation
                self._validate_band(contact, result)

                # 6. Mode validation
                self._validate_mode(contact, result)

            # Collect errors and warnings
            if result.errors:
                all_errors.extend(result.errors)
            if result.warnings:
                all_warnings.extend(result.warnings)

            results.append(result)

        # Update database with validation results
        self._update_database(results)

        # Create summary
        valid_count = sum(1 for r in results if r.is_valid and not r.is_duplicate)
        duplicate_count = sum(1 for r in results if r.is_duplicate)
        invalid_count = sum(1 for r in results if not r.is_valid and not r.is_duplicate)

        summary = {
            'total_contacts': len(contacts),
            'valid_contacts': valid_count,
            'duplicate_contacts': duplicate_count,
            'invalid_contacts': invalid_count,
            'errors': all_errors,
            'warnings': all_warnings
        }

        logger.info(
            f"Validation complete for log {log_id}: "
            f"{valid_count} valid, {duplicate_count} duplicates, {invalid_count} invalid"
        )

        return summary

    def _validate_exchange(self, contact: Contact, result: ValidationResult):
        """Validate exchange format (RS/RST and CQ zone)"""

        # Validate RS/RST
        rst = contact.rst_received
        if not rst:
            result.add_error("Missing RST")
        else:
            if contact.mode == 'CW':
                # CW should be 3 digits (e.g., 599)
                if not re.match(r'^[1-5][1-9][1-9]$', rst):
                    result.add_error(f"Invalid RST for CW: '{rst}' (expected 3 digits like 599)")
            elif contact.mode in ['SSB', 'PH']:
                # SSB should be 2 digits (e.g., 59)
                if not re.match(r'^[1-5][1-9]$', rst):
                    result.add_error(f"Invalid RS for SSB: '{rst}' (expected 2 digits like 59)")

        # Validate CQ Zone
        zone = contact.exchange_received
        if not zone:
            result.add_error("Missing CQ zone in exchange")
        else:
            zone_str = extract_cq_zone(zone)
            if zone_str is None:
                result.add_error(f"Invalid CQ zone format: '{zone}' (must be a number 1-40)")

    def _validate_callsign(self, contact: Contact, result: ValidationResult):
        """Validate callsign format"""

        callsign = contact.call_received
        if not callsign:
            result.add_error("Missing callsign")
            return

        # Basic callsign pattern: prefix + number + suffix
        # Can include /P, /M, /MM, /AM, etc.
        # Examples: W1AW, G4OPE, LU1ABC, PY2AA/1, EA8/DL1ABC

        # Very basic check - at least one letter and one number
        if not re.search(r'[A-Z]', callsign.upper()):
            result.add_error(f"Invalid callsign: '{callsign}' (no letters)")
        elif not re.search(r'\d', callsign):
            result.add_error(f"Invalid callsign: '{callsign}' (no numbers)")

        # Check for obviously invalid characters
        if re.search(r'[^A-Z0-9/]', callsign.upper()):
            result.add_error(f"Invalid callsign: '{callsign}' (invalid characters)")

        # Warn about special suffixes
        if '/MM' in callsign.upper() or '/AM' in callsign.upper():
            result.add_warning(f"Mobile station: {callsign}")

    def _validate_time(self, contact: Contact, start: datetime, end: datetime,
                      result: ValidationResult):
        """Validate contact time is within contest period"""

        qso_time = contact.qso_datetime
        if not qso_time:
            result.add_error("Missing QSO datetime")
            return

        if qso_time < start:
            result.add_error(
                f"QSO before contest start: {qso_time} < {start}"
            )
        elif qso_time > end:
            result.add_error(
                f"QSO after contest end: {qso_time} > {end}"
            )

    def _validate_band(self, contact: Contact, result: ValidationResult):
        """Validate band is allowed in contest"""

        if not contact.band:
            result.add_error("Missing band")
            return

        allowed_bands = self.rules.contest.bands
        if allowed_bands and contact.band not in allowed_bands:
            result.add_error(
                f"Invalid band: {contact.band} (allowed: {', '.join(allowed_bands)})"
            )

    def _validate_mode(self, contact: Contact, result: ValidationResult):
        """Validate mode is allowed in contest"""

        if not contact.mode:
            result.add_error("Missing mode")
            return

        # Normalize mode (PH = SSB)
        mode = 'SSB' if contact.mode == 'PH' else contact.mode

        allowed_modes = self.rules.contest.modes
        if allowed_modes and mode not in allowed_modes:
            result.add_error(
                f"Invalid mode: {contact.mode} (allowed: {', '.join(allowed_modes)})"
            )

    def _update_database(self, results: List[ValidationResult]):
        """Update database with validation results"""

        for result in results:
            if result.is_duplicate:
                # Mark as duplicate
                self.contact_repo.mark_as_duplicate(result.contact_id)
            elif not result.is_valid:
                # Mark as invalid
                self.contact_repo.update_validation(
                    result.contact_id,
                    is_valid=False,
                    validation_status=result.validation_status,
                    validation_message=result.get_message()
                )
            else:
                # Mark as valid (may have warnings)
                message = result.get_message()
                if message:
                    self.contact_repo.update_validation(
                        result.contact_id,
                        is_valid=True,
                        validation_status='valid',
                        validation_message=message
                    )

        logger.info(f"Updated {len(results)} contacts in database")


class BatchValidator:
    """Validate multiple logs in batch"""

    def __init__(self, contact_repo: ContactRepository, rules: ContestRules):
        self.validator = ContactValidator(contact_repo, rules)

    def validate_contest(self, log_ids: List[int],
                        contest_start: datetime = None,
                        contest_end: datetime = None) -> Dict[str, any]:
        """
        Validate all logs in a contest.

        Args:
            log_ids: List of log IDs to validate
            contest_start: Contest start datetime
            contest_end: Contest end datetime

        Returns:
            Summary of validation results
        """
        total_contacts = 0
        total_valid = 0
        total_duplicates = 0
        total_invalid = 0

        log_results = []

        for log_id in log_ids:
            logger.info(f"Validating log {log_id}")
            result = self.validator.validate_log(log_id, contest_start, contest_end)

            total_contacts += result['total_contacts']
            total_valid += result['valid_contacts']
            total_duplicates += result['duplicate_contacts']
            total_invalid += result['invalid_contacts']

            log_results.append({
                'log_id': log_id,
                'result': result
            })

        return {
            'total_logs': len(log_ids),
            'total_contacts': total_contacts,
            'valid_contacts': total_valid,
            'duplicate_contacts': total_duplicates,
            'invalid_contacts': total_invalid,
            'log_results': log_results
        }

