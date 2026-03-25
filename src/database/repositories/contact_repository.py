"""
Repository for Contact (QSO) database operations
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

from ..models import Contact as DBContact
from ...core.models.contact import ContactBase

logger = logging.getLogger(__name__)


class ContactRepository:
    """Repository for contact/QSO CRUD operations"""

    def __init__(self, session: Session):
        """
        Initialize contact repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, contact_data: ContactBase, log_id: int) -> DBContact:
        """
        Create a new contact entry in the database.

        Args:
            contact_data: Contact data from parser (Pydantic model)
            log_id: ID of the log this contact belongs to

        Returns:
            Created Contact database object
        """
        try:
            # Parse datetime from date and time strings
            qso_datetime = self._parse_datetime(
                contact_data.qso_date,
                contact_data.qso_time
            )

            # Determine band from frequency
            band = self._frequency_to_band(contact_data.frequency)

            # Check if contact has validation issues from parser
            has_validation_issues = hasattr(contact_data, 'validation_reason') and contact_data.validation_reason
            validation_status = 'invalid_exchange' if has_validation_issues else 'valid'
            is_valid = not has_validation_issues

            # Create database contact object
            db_contact = DBContact(
                log_id=log_id,

                # QSO details
                frequency=contact_data.frequency,
                mode=contact_data.mode,
                qso_date=contact_data.qso_date,
                qso_time=contact_data.qso_time,
                band=band,
                qso_datetime=qso_datetime,

                # Sent information
                call_sent=contact_data.call_sent,
                rst_sent=contact_data.rst_sent,
                exchange_sent=contact_data.exchange_sent,

                # Received information
                call_received=contact_data.call_received,
                rst_received=contact_data.rst_received,
                exchange_received=contact_data.exchange_received,

                # Optional
                transmitter_id=contact_data.transmitter_id,

                # Scoring fields (will be populated later by scoring engine)
                points=None,
                is_multiplier=False,
                multiplier_type=None,
                multiplier_value=None,

                # Validation (will be set from parser or updated by validation engine)
                is_valid=is_valid,
                is_duplicate=False,
                validation_status=validation_status,
                validation_notes=contact_data.validation_reason if has_validation_issues else None,
            )

            self.session.add(db_contact)
            self.session.flush()  # Get the ID without committing

            return db_contact

        except SQLAlchemyError as e:
            logger.error(f"Error creating contact: {e}")
            raise

    def create_batch(self, contacts_data: List[ContactBase], log_id: int) -> List[DBContact]:
        """
        Create multiple contacts in batch for better performance.

        Args:
            contacts_data: List of contact data from parser
            log_id: ID of the log these contacts belong to

        Returns:
            List of created Contact database objects
        """
        try:
            db_contacts = []

            for contact_data in contacts_data:
                qso_datetime = self._parse_datetime(
                    contact_data.qso_date,
                    contact_data.qso_time
                )
                band = self._frequency_to_band(contact_data.frequency)

                # Check if contact has validation issues from parser
                has_validation_issues = hasattr(contact_data, 'validation_reason') and contact_data.validation_reason
                validation_status = 'invalid_exchange' if has_validation_issues else 'valid'
                is_valid = not has_validation_issues

                db_contact = DBContact(
                    log_id=log_id,
                    frequency=contact_data.frequency,
                    mode=contact_data.mode,
                    qso_date=contact_data.qso_date,
                    qso_time=contact_data.qso_time,
                    band=band,
                    qso_datetime=qso_datetime,
                    call_sent=contact_data.call_sent,
                    rst_sent=contact_data.rst_sent,
                    exchange_sent=contact_data.exchange_sent,
                    call_received=contact_data.call_received,
                    rst_received=contact_data.rst_received,
                    exchange_received=contact_data.exchange_received,
                    transmitter_id=contact_data.transmitter_id,
                    is_valid=is_valid,
                    is_duplicate=False,
                    validation_status=validation_status,
                    validation_notes=contact_data.validation_reason if has_validation_issues else None,
                )
                db_contacts.append(db_contact)

            self.session.add_all(db_contacts)
            self.session.flush()

            logger.info(f"Created {len(db_contacts)} contacts for log {log_id}")
            return db_contacts

        except SQLAlchemyError as e:
            logger.error(f"Error creating contacts batch: {e}")
            raise

    def get_by_id(self, contact_id: int) -> Optional[DBContact]:
        """Get contact by ID"""
        return self.session.query(DBContact).filter(DBContact.id == contact_id).first()

    def get_all_for_log(self, log_id: int) -> List[DBContact]:
        """Get all contacts for a specific log"""
        return self.session.query(DBContact).filter(
            DBContact.log_id == log_id
        ).order_by(DBContact.qso_datetime).all()

    def get_valid_for_log(self, log_id: int) -> List[DBContact]:
        """Get all valid contacts for a log"""
        return self.session.query(DBContact).filter(
            DBContact.log_id == log_id,
            DBContact.is_valid == True
        ).all()

    def update_validation(self, contact_id: int, is_valid: bool,
                         validation_status: str, validation_message: str = None) -> DBContact:
        """Update contact validation status"""
        db_contact = self.get_by_id(contact_id)
        if db_contact:
            db_contact.is_valid = is_valid
            db_contact.validation_status = validation_status
            db_contact.validation_notes = validation_message
            self.session.flush()
        return db_contact

    def update_scoring(self, contact_id: int, points: int,
                      is_multiplier: bool = False,
                      multiplier_type: str = None,
                      multiplier_value: str = None) -> DBContact:
        """Update contact scoring information"""
        db_contact = self.get_by_id(contact_id)
        if db_contact:
            db_contact.points = points
            db_contact.is_multiplier = is_multiplier
            db_contact.multiplier_type = multiplier_type
            db_contact.multiplier_value = multiplier_value
            self.session.flush()
        return db_contact

    def mark_as_duplicate(self, contact_id: int) -> DBContact:
        """Mark a contact as duplicate"""
        db_contact = self.get_by_id(contact_id)
        if db_contact:
            db_contact.is_duplicate = True
            db_contact.validation_status = 'duplicate'
            db_contact.points = 0
            self.session.flush()
        return db_contact

    def _parse_datetime(self, qso_date: str, qso_time: str) -> datetime:
        """
        Parse QSO date and time into datetime object.

        Args:
            qso_date: Date string in YYYY-MM-DD format
            qso_time: Time string in HHMM format

        Returns:
            datetime object
        """
        try:
            # Combine date and time
            date_str = f"{qso_date} {qso_time[:2]}:{qso_time[2:4]}"
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        except ValueError as e:
            logger.warning(f"Error parsing datetime {qso_date} {qso_time}: {e}")
            # Return a default datetime if parsing fails
            return datetime.now()

    def _frequency_to_band(self, frequency_khz: int) -> str:
        """
        Convert frequency in kHz to band name.

        Args:
            frequency_khz: Frequency in kHz

        Returns:
            Band name (e.g., '10m')
        """
        # Common amateur radio bands
        if 1800 <= frequency_khz <= 2000:
            return '160m'
        elif 3500 <= frequency_khz <= 4000:
            return '80m'
        elif 7000 <= frequency_khz <= 7300:
            return '40m'
        elif 10100 <= frequency_khz <= 10150:
            return '30m'
        elif 14000 <= frequency_khz <= 14350:
            return '20m'
        elif 18068 <= frequency_khz <= 18168:
            return '17m'
        elif 21000 <= frequency_khz <= 21450:
            return '15m'
        elif 24890 <= frequency_khz <= 24990:
            return '12m'
        elif 28000 <= frequency_khz <= 29700:
            return '10m'
        elif 50000 <= frequency_khz <= 54000:
            return '6m'
        elif 144000 <= frequency_khz <= 148000:
            return '2m'
        elif 420000 <= frequency_khz <= 450000:
            return '70cm'
        else:
            return 'unknown'

