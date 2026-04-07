"""
Scoring Service - Orchestrates contest scoring

This service bridges the database layer with the rules engine to:
1. Load contest rules and log data from database
2. Process contacts through the rules engine
3. Calculate scores and multipliers
4. Store results back to database

Uses the existing RulesEngine for all scoring logic.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from ..database.models import Log, Contact, Score
from ..core.rules.rules_engine import RulesEngine, Contact as RulesContact
from ..core.rules.rules_loader import RulesLoader
from .callsign_lookup import CallsignLookupService
from ..utils import normalize_cq_zone


class ScoringService:
    """Service for processing contest scoring"""

    def __init__(self, session: Session, contest_slug: str):
        """
        Initialize scoring service
        
        Args:
            session: Database session
            contest_slug: Contest identifier (e.g., "sa10m")
        """
        self.session = session
        self.contest_slug = contest_slug
        
        # Load contest rules
        loader = RulesLoader()
        self.rules = loader.load_contest(contest_slug)

    def score_log(self, log_id: int) -> Dict:
        """
        Score a complete log entry
        
        Args:
            log_id: Database ID of log to score
            
        Returns:
            Dictionary with scoring results
        """
        # Load log and contacts from database
        log = self.session.get(Log, log_id)
        if not log:
            raise ValueError(f"Log {log_id} not found")

        # Check logs are used only to validate others — they receive no score
        if (log.category_operator or "").upper() == "CHECKLOG":
            self._store_checklog_zero_score(log_id, log)
            return {"checklog": True, "final_score": 0, "total_qsos": 0, "valid_qsos": 0,
                    "duplicate_qsos": 0, "total_points": 0, "wpx_multipliers": 0,
                    "zone_multipliers": 0, "band_scores": {}}

        # Load contacts ordered by datetime
        # Note: Use text() to avoid enum validation issues with legacy data
        from sqlalchemy import text
        stmt = text("""
            SELECT * FROM contacts 
            WHERE log_id = :log_id 
            ORDER BY qso_datetime
        """)
        result = self.session.execute(stmt, {"log_id": log_id})
        
        # Manually convert rows to Contact objects (bypassing enum validation)
        contacts = []
        for row in result:
            contact = Contact()
            validation_status = None
            for key, value in row._mapping.items():
                # Store validation_status separately to check later
                if key == 'validation_status':
                    validation_status = value
                    continue
                setattr(contact, key, value)
            
            # Store validation_status as string attribute for checking
            contact.validation_status_str = validation_status
            contacts.append(contact)

        if not contacts:
            raise ValueError(f"No contacts found for log {log_id}")

        # Extract operator info from log
        operator_info = self._extract_operator_info(log)
        operator_info['callsign'] = log.callsign

        # Initialize callsign lookup service
        callsign_lookup = CallsignLookupService(self.session)

        # Initialize rules engine
        engine = RulesEngine(
            rules=self.rules,
            operator_info=operator_info,
            callsign_lookup=callsign_lookup
        )

        # Process all contacts
        processed_contacts = []
        rules_contacts = []
        for db_contact in contacts:
            # Convert database contact to rules engine contact
            rules_contact = self._db_contact_to_rules_contact(db_contact)
            
            # Process through rules engine
            result = engine.process_contact(rules_contact)
            
            processed_contacts.append((db_contact, result))
            rules_contacts.append(result)

        # Calculate final score
        score_breakdown = engine.calculate_final_score(rules_contacts)

        # Update database with results
        self._update_contacts_with_results(processed_contacts)
        self._update_score_table(log_id, log, score_breakdown, engine)

        return score_breakdown

    def _extract_operator_info(self, log: Log) -> Dict[str, str]:
        """
        Extract operator information from log using CTY data lookup
        
        Args:
            log: Log database model
            
        Returns:
            Dictionary with operator DXCC, continent, and zone
        """
        # Use callsign lookup to get operator info from CTY data
        callsign_lookup = CallsignLookupService(self.session)
        operator_info = callsign_lookup.lookup_callsign(log.callsign)
        
        if operator_info:
            return {
                'dxcc': operator_info.get('dxcc_code', 0),
                'continent': operator_info.get('continent', ''),
                'cq_zone': operator_info.get('cq_zone', 0),
                'country_name': operator_info.get('country_name', '')
            }
        
        # Fallback if not found in CTY data
        return {
            'dxcc': 0,
            'continent': '',
            'cq_zone': 0,
            'country_name': ''
        }

    def _db_contact_to_rules_contact(self, db_contact: Contact) -> RulesContact:
        """
        Convert database Contact to RulesEngine Contact
        
        Args:
            db_contact: Database contact model
            
        Returns:
            RulesContact object with cached continent data if available
        """
        # In the database, RST and exchange are already separated:
        # - rst_sent/rst_received contains the signal report (e.g., "59", "599")
        # - exchange_sent/exchange_received contains just the zone (e.g., "12", "05")
        
        # Normalize zone by removing leading zeros
        zone_sent = normalize_cq_zone(db_contact.exchange_sent) or '0'
        zone_received = normalize_cq_zone(db_contact.exchange_received) or '0'
        
        exchange_sent = {
            'rs_rst': db_contact.rst_sent,
            'cq_zone': zone_sent
        }
        
        exchange_received = {
            'rs_rst': db_contact.rst_received,
            'cq_zone': zone_received
        }
        
        rules_contact = RulesContact(
            timestamp=db_contact.qso_datetime,
            callsign=db_contact.call_received,
            band=db_contact.band,
            mode=db_contact.mode,
            frequency=db_contact.frequency,
            rst_sent=db_contact.rst_sent,
            rst_received=db_contact.rst_received,
            exchange_sent=exchange_sent,
            exchange_received=exchange_received
        )
        
        # Add validation errors if present
        validation_status = getattr(db_contact, 'validation_status_str', 'VALID')
        if validation_status and validation_status.lower() in [
            'not_in_log', 'busted_call', 'invalid_callsign',
            'invalid_exchange', 'invalid',
            'time_mismatch', 'exchange_mismatch'
        ]:
            rules_contact.validation_errors.append(validation_status)
        
        # Add cached continent if available (avoid lookup during scoring)
        if hasattr(db_contact, 'contact_continent') and db_contact.contact_continent:
            rules_contact._cached_continent = db_contact.contact_continent
        
        return rules_contact

    def _update_contacts_with_results(
        self, 
        processed_contacts: List[Tuple[Contact, 'RulesContact']]
    ) -> None:
        """
        Update contact records with scoring results using explicit SQL UPDATE
        
        Args:
            processed_contacts: List of (db_contact, rules_contact) tuples
        """
        from sqlalchemy import text
        
        for db_contact, rules_contact in processed_contacts:
            # Check validation status from cross-check
            validation_status = getattr(db_contact, 'validation_status_str', 'VALID')
            is_invalid = validation_status and validation_status.lower() in [
                'not_in_log', 'busted_call', 'invalid_callsign',
                'invalid_exchange', 'invalid',
                'time_mismatch', 'exchange_mismatch'
            ]
            
            # Determine flags
            is_duplicate = rules_contact.is_duplicate
            
            if is_invalid:
                is_valid = False
            else:
                is_valid = not is_duplicate
            
            # Prepare multiplier information
            is_multiplier = rules_contact.is_multiplier
            multiplier_type = None
            multiplier_value = None
            
            if rules_contact.is_multiplier:
                # Store multiplier types
                multiplier_type = ','.join(rules_contact.multiplier_types)
                
                # Store multiplier values (extract from exchange or callsign)
                values = []
                if 'wpx_prefix' in rules_contact.multiplier_types:
                    # Extract WPX prefix from callsign
                    from ..core.rules.rules_engine import RulesEngine
                    prefix = RulesEngine._extract_wpx_prefix(None, rules_contact.callsign)
                    if prefix:
                        values.append(prefix)
                if 'cq_zone' in rules_contact.multiplier_types:
                    # Get zone from exchange
                    zone = rules_contact.exchange_received.get('cq_zone', '')
                    if zone:
                        values.append(zone)
                multiplier_value = ','.join(values) if values else None
            
            # Use explicit SQL UPDATE to ensure persistence
            self.session.execute(
                text("""
                    UPDATE contacts 
                    SET points = :points,
                        is_duplicate = :is_duplicate,
                        is_valid = :is_valid,
                        is_multiplier = :is_multiplier,
                        multiplier_type = :multiplier_type,
                        multiplier_value = :multiplier_value
                    WHERE id = :contact_id
                """),
                {
                    'points': rules_contact.points,
                    'is_duplicate': is_duplicate,
                    'is_valid': is_valid,
                    'is_multiplier': is_multiplier,
                    'multiplier_type': multiplier_type,
                    'multiplier_value': multiplier_value,
                    'contact_id': db_contact.id
                }
            )

        # Commit all updates
        self.session.commit()

    def _store_checklog_zero_score(self, log_id: int, log: Log) -> None:
        """Store a zeroed score record for a check log and mark it scored."""
        from sqlalchemy import select
        stmt = select(Score).where(Score.log_id == log_id)
        score = self.session.execute(stmt).scalar_one_or_none()
        if not score:
            score = Score(log_id=log_id)
            self.session.add(score)
        score.total_qsos = 0
        score.valid_qsos = 0
        score.duplicate_qsos = 0
        score.total_points = 0
        score.multipliers = 0
        score.final_score = 0
        score.points_by_band = {}
        score.qsos_by_band = {}
        score.multipliers_by_band = {}
        score.multipliers_list = []
        score.calculated_at = datetime.utcnow()
        score.calculation_version = "1.0"
        score.notes = "Check log — not scored"
        from src.database.models import ContestStatus
        log.status = ContestStatus.SCORED
        log.processed_at = datetime.utcnow()
        self.session.commit()

    def _update_score_table(
        self,
        log_id: int,
        log: Log,
        score_breakdown: Dict,
        engine: RulesEngine
    ) -> None:
        """
        Update or create score record
        
        Args:
            log_id: Log database ID
            log: Log model
            score_breakdown: Score calculation results
            engine: RulesEngine instance with state
        """
        # Check if score record exists (query by log_id field, not primary key)
        stmt = select(Score).where(Score.log_id == log_id)
        score = self.session.execute(stmt).scalar_one_or_none()
        if not score:
            score = Score(log_id=log_id)
            self.session.add(score)        # Basic counts
        score.total_qsos = score_breakdown['total_qsos']
        score.valid_qsos = score_breakdown['valid_qsos']
        score.duplicate_qsos = score_breakdown['duplicate_qsos']

        # Count invalid and NIL QSOs directly from the contacts table so we
        # pick up ALL invalid statuses (INVALID_EXCHANGE, OUT_OF_PERIOD, etc.)
        # regardless of case, and don't depend on cross-check having run first.
        # NOTE: 'unique_call' is NOT invalid — it means the other station didn't
        # submit a log, but the QSO is still valid and scores points.
        from sqlalchemy import text as _t
        qso_counts = self.session.execute(_t("""
            SELECT
                SUM(CASE WHEN UPPER(validation_status) NOT IN ('VALID','DUPLICATE','UNIQUE_CALL')
                         AND validation_status IS NOT NULL THEN 1 ELSE 0 END),
                SUM(CASE WHEN UPPER(validation_status) = 'NOT_IN_LOG' THEN 1 ELSE 0 END)
            FROM contacts WHERE log_id = :log_id
        """), {"log_id": log_id}).fetchone()
        score.invalid_qsos = qso_counts[0] or 0
        score.not_in_log_qsos = qso_counts[1] or 0
        
        # Points and multipliers
        score.total_points = score_breakdown['total_points']
        score.multipliers = score_breakdown['wpx_multipliers'] + score_breakdown['zone_multipliers']
        score.final_score = score_breakdown['final_score']

        # Detailed breakdowns from band_scores
        points_by_band = {}
        qsos_by_band = {}
        zones_by_band = {}
        
        for band, band_data in score_breakdown['band_scores'].items():
            points_by_band[band] = band_data['points']
            qsos_by_band[band] = band_data['qsos']
            zones_by_band[band] = band_data['zones_on_band']
        
        score.points_by_band = points_by_band
        score.qsos_by_band = qsos_by_band
        score.multipliers_by_band = zones_by_band  # Store zones per band for reference

        # Multipliers list - combine prefixes and zones
        multipliers_list = list(engine.worked_prefixes)
        # Add all unique zones (not per band since this is contest-wide)
        all_zones = set()
        for zones in engine.worked_zones_per_band.values():
            all_zones.update(zones)
        multipliers_list.extend([f"Zone_{zone}" for zone in sorted(all_zones)])
        score.multipliers_list = multipliers_list

        # Metadata
        score.calculated_at = datetime.utcnow()
        score.calculation_version = "1.0"
        score.notes = f"Scored using {self.contest_slug} rules"

        # Mark log as scored
        from src.database.models import ContestStatus
        log.status = ContestStatus.SCORED
        log.processed_at = datetime.utcnow()

        self.session.commit()

    def score_all_logs(self, contest_id: int) -> List[Dict]:
        """
        Score all logs for a contest
        
        Args:
            contest_id: Contest database ID
            
        Returns:
            List of score breakdowns for all logs
        """
        # Get all logs for contest
        from src.database.models import ContestStatus
        stmt = select(Log).where(
            Log.contest_id == contest_id,
            Log.status.in_([ContestStatus.VALIDATED, ContestStatus.SCORED, ContestStatus.PENDING])
        )
        logs = self.session.execute(stmt).scalars().all()

        results = []
        for log in logs:
            print(f"Scoring {log.callsign}...")
            try:
                score_breakdown = self.score_log(log.id)
                results.append({
                    'callsign': log.callsign,
                    'status': 'success',
                    'score': score_breakdown['final_score'],
                    'qsos': score_breakdown['total_qsos']
                })
            except Exception as e:
                print(f"Error scoring {log.callsign}: {e}")
                results.append({
                    'callsign': log.callsign,
                    'status': 'error',
                    'error': str(e)
                })

        return results

    def get_score_summary(self, log_id: int) -> Optional[Dict]:
        """
        Get score summary for a log
        
        Args:
            log_id: Log database ID
            
        Returns:
            Score summary dictionary or None if not scored
        """
        score = self.session.get(Score, log_id)
        if not score:
            return None

        log = self.session.get(Log, log_id)

        return {
            'callsign': log.callsign,
            'total_qsos': score.total_qsos,
            'valid_qsos': score.valid_qsos,
            'duplicate_qsos': score.duplicate_qsos,
            'total_points': score.total_points,
            'multipliers': score.multipliers,
            'final_score': score.final_score,
            'points_by_band': score.points_by_band,
            'points_by_mode': score.points_by_mode,
            'multipliers_list': score.multipliers_list,
            'calculated_at': score.calculated_at
        }
