"""
Repository for Log (Station) database operations
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from ..models import Log as DBLog, Contest
from ...core.models.log import LogBase

logger = logging.getLogger(__name__)


class LogRepository:
    """Repository for log/station CRUD operations"""

    def __init__(self, session: Session):
        """
        Initialize log repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, log_data: LogBase, contest_id: int) -> DBLog:
        """
        Create a new log entry in the database.

        Args:
            log_data: Log data from parser (Pydantic model)
            contest_id: ID of the contest this log belongs to

        Returns:
            Created Log database object
        """
        try:
            # Create database log object
            db_log = DBLog(
                contest_id=contest_id,
                callsign=log_data.callsign,
                location=log_data.location,
                club=log_data.club,

                # Categories
                category_operator=log_data.category_operator,
                category_assisted=log_data.category_assisted,
                category_band=log_data.category_band,
                category_mode=log_data.category_mode,
                category_power=log_data.category_power,
                category_station=log_data.category_station,
                category_transmitter=log_data.category_transmitter,
                category_overlay=log_data.category_overlay,
                category_time=log_data.category_time,

                # Operator info
                operators=log_data.operators,
                name=log_data.name,

                # Address
                address=log_data.address,
                address_city=log_data.address_city,
                address_state_province=log_data.address_state_province,
                address_postalcode=log_data.address_postalcode,
                address_country=log_data.address_country,

                # Other
                grid_locator=log_data.grid_locator,
                email=log_data.email,

                # Cabrillo-specific
                claimed_score=getattr(log_data, 'claimed_score', None),

                # Metadata
                created_at=None,  # Will use database default
                updated_at=None,
            )

            self.session.add(db_log)
            self.session.flush()  # Get the ID without committing

            logger.info(f"Created log entry for {log_data.callsign} (ID: {db_log.id})")
            return db_log

        except SQLAlchemyError as e:
            logger.error(f"Error creating log: {e}")
            raise

    def get_by_id(self, log_id: int) -> Optional[DBLog]:
        """Get log by ID"""
        return self.session.query(DBLog).filter(DBLog.id == log_id).first()

    def get_by_callsign(self, callsign: str, contest_id: int) -> Optional[DBLog]:
        """Get log by callsign and contest"""
        return self.session.query(DBLog).filter(
            DBLog.callsign == callsign,
            DBLog.contest_id == contest_id
        ).first()

    def get_all(self) -> List[DBLog]:
        """Get all logs"""
        return self.session.query(DBLog).all()

    def get_all_for_contest(self, contest_id: int) -> List[DBLog]:
        """Get all logs for a specific contest"""
        return self.session.query(DBLog).filter(
            DBLog.contest_id == contest_id
        ).all()


    def update_score(self, log_id: int, final_score: int, qso_count: int,
                     multiplier_count: int) -> DBLog:
        """Update log with calculated scores"""
        db_log = self.get_by_id(log_id)
        if db_log:
            db_log.final_score = final_score
            db_log.qso_count = qso_count
            db_log.multiplier_count = multiplier_count
            self.session.flush()
            logger.info(f"Updated scores for log {log_id}")
        return db_log

    def delete(self, log_id: int) -> bool:
        """Delete a log and all its contacts"""
        db_log = self.get_by_id(log_id)
        if db_log:
            self.session.delete(db_log)
            self.session.flush()
            logger.info(f"Deleted log {log_id}")
            return True
        return False

