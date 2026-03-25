"""
SQLAlchemy Database Models for Contest Management System

Based on Cabrillo log format v3.0 specification and SA10M contest requirements.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class ContestStatus(str, enum.Enum):
    """Contest processing status"""
    PENDING = "pending"
    VALIDATED = "validated"
    SCORED = "scored"
    PUBLISHED = "published"
    ERROR = "error"


class ValidationStatus(str, enum.Enum):
    """QSO validation status"""
    VALID = "valid"
    DUPLICATE = "duplicate"
    INVALID = "invalid"  # General invalid status
    INVALID_CALLSIGN = "invalid_callsign"
    INVALID_EXCHANGE = "invalid_exchange"
    OUT_OF_PERIOD = "out_of_period"
    INVALID_BAND = "invalid_band"
    INVALID_MODE = "invalid_mode"
    NOT_IN_LOG = "not_in_log"
    TIME_MISMATCH = "time_mismatch"
    EXCHANGE_MISMATCH = "exchange_mismatch"


class Contest(Base):
    """
    Contest definition table
    Stores information about specific contest instances
    """
    __tablename__ = "contests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # e.g., "SA10M Contest"
    slug = Column(String(50), unique=True, nullable=False)  # e.g., "sa10m"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    rules_file = Column(String(200), nullable=False)  # Path to YAML rules
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    logs = relationship("Log", back_populates="contest", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Contest(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class Log(Base):
    """
    Log submission table
    Stores Cabrillo log header information and metadata
    """
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)

    # Cabrillo Header Fields (https://wwrof.org/cabrillo/cabrillo-specification-v3/)
    cabrillo_version = Column(String(10), default="3.0")  # START-OF-LOG
    callsign = Column(String(20), nullable=False)
    location = Column(String(50))  # DX, SA, etc.
    club = Column(String(100))
    contest_name = Column(String(100))  # CONTEST field from Cabrillo

    # Category fields
    category_operator = Column(String(50))  # SINGLE-OP, MULTI-OP, etc.
    category_assisted = Column(String(50))  # ASSISTED, NON-ASSISTED
    category_band = Column(String(20))  # 10M, ALL, etc.
    category_mode = Column(String(20))  # SSB, CW, MIXED
    category_power = Column(String(20))  # HIGH, LOW, QRP
    category_station = Column(String(50))  # FIXED, MOBILE, PORTABLE, etc.
    category_transmitter = Column(String(20))  # ONE, TWO, etc.
    category_overlay = Column(String(50))  # TB-WIRES, ROOKIE, etc.
    category_time = Column(String(20))  # 6-HOURS, 12-HOURS, 24-HOURS

    # Operator/Station Info
    operators = Column(Text)  # Comma-separated list of operators
    name = Column(String(200))  # Operator name
    address = Column(Text)  # Full address (multi-line)
    address_city = Column(String(100))
    address_state_province = Column(String(100))
    address_postalcode = Column(String(20))
    address_country = Column(String(100))
    grid_locator = Column(String(10))  # Maidenhead grid
    email = Column(String(200))

    # Scores and Statistics
    claimed_score = Column(Integer)

    # Software/Processing Info
    created_by = Column(String(200))  # Logging software used
    submitted_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(Text)  # Original file location
    file_hash = Column(String(64))  # SHA256 hash for duplicate detection
    file_modified_at = Column(DateTime)  # File modification timestamp

    # Processing Status
    status = Column(Enum(ContestStatus), default=ContestStatus.PENDING, nullable=False)
    validation_notes = Column(Text)
    processed_at = Column(DateTime)

    # Additional metadata
    extra_data = Column(JSON)  # For any additional Cabrillo fields

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contest = relationship("Contest", back_populates="logs")
    contacts = relationship("Contact", back_populates="log", cascade="all, delete-orphan")
    score = relationship("Score", back_populates="log", uselist=False, cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_log_contest_callsign", "contest_id", "callsign"),
        Index("idx_log_status", "status"),
        Index("idx_log_file_hash", "file_hash"),
    )

    def __repr__(self):
        return f"<Log(id={self.id}, callsign='{self.callsign}', status='{self.status}')>"


class Contact(Base):
    """
    QSO/Contact table
    Stores individual contacts from Cabrillo QSO lines

    Cabrillo QSO Format:
    QSO: freq mo date time call-sent rst-sent exch-sent call-rcvd rst-rcvd exch-rcvd t
    Example:
    QSO:   28300 PH 2025-03-08 1207 CE1KR         59   12   DP7D          59   14
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(Integer, ForeignKey("logs.id"), nullable=False)

    # QSO Details
    frequency = Column(Integer, nullable=False)  # in kHz
    mode = Column(String(10), nullable=False)  # PH (SSB), CW, RY (RTTY), DG (Digital)
    qso_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    qso_time = Column(String(4), nullable=False)  # HHMM UTC format
    qso_datetime = Column(DateTime, nullable=False)  # Combined datetime for queries

    # Transmitter (Sent) Information
    call_sent = Column(String(20), nullable=False)  # Own callsign
    rst_sent = Column(String(10), nullable=False)  # Signal report sent
    exchange_sent = Column(String(50), nullable=False)  # Exchange data sent (e.g., province)

    # Receiver (Received) Information
    call_received = Column(String(20), nullable=False)  # Other station's callsign
    rst_received = Column(String(10), nullable=False)  # Signal report received
    exchange_received = Column(String(50), nullable=False)  # Exchange data received

    # Transmitter ID (optional, for multi-transmitter)
    transmitter_id = Column(String(5))  # 0, 1, etc.

    # Derived/Computed Fields
    band = Column(String(10))  # Derived from frequency: 10m, 20m, etc.

    # Scoring and Validation
    points = Column(Integer, default=0)
    is_multiplier = Column(Boolean, default=False)
    multiplier_type = Column(String(50))  # province, country, zone, etc.
    multiplier_value = Column(String(50))  # The actual multiplier (e.g., "BA", "W")
    
    # Cached lookup data for performance
    contact_continent = Column(String(2))  # SA, NA, EU, AS, AF, OC - cached from CTY lookup
    contact_country = Column(String(100))  # Country name - cached from CTY lookup
    wpx_prefix = Column(String(10))  # WPX prefix extracted from callsign

    # Validation Status
    is_valid = Column(Boolean, default=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.VALID)
    validation_notes = Column(Text)

    # Cross-checking fields (for matching with other station's log)
    matched_contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    time_diff_seconds = Column(Integer)  # Time difference with matched contact
    frequency_diff_khz = Column(Integer)  # Frequency difference with matched contact

    # Metadata
    extra_data = Column(JSON)  # For any additional fields

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    log = relationship("Log", back_populates="contacts")
    duplicate_of = relationship("Contact", remote_side=[id], foreign_keys=[duplicate_of_id])
    matched_contact = relationship("Contact", remote_side=[id], foreign_keys=[matched_contact_id])

    # Indexes for performance
    __table_args__ = (
        Index("idx_contact_log_id", "log_id"),
        Index("idx_contact_datetime", "qso_datetime"),
        Index("idx_contact_callsign", "call_received"),
        Index("idx_contact_band_mode", "band", "mode"),
        Index("idx_contact_valid", "is_valid"),
        Index("idx_contact_duplicate", "is_duplicate"),
        Index("idx_contact_log_datetime", "log_id", "qso_datetime"),
        Index("idx_contact_continent", "contact_continent"),  # For fast continent filtering
        Index("idx_contact_wpx", "wpx_prefix"),  # For fast WPX multiplier counting
        # NOTE: No unique constraint - duplicates are allowed and marked during validation
    )

    def __repr__(self):
        return (f"<Contact(id={self.id}, callsign='{self.call_received}', "
                f"datetime='{self.qso_datetime}', band='{self.band}', mode='{self.mode}')>")


class Score(Base):
    """
    Score calculation table
    Stores final scores and breakdowns for each log
    """
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(Integer, ForeignKey("logs.id"), unique=True, nullable=False)

    # QSO Statistics
    total_qsos = Column(Integer, default=0, nullable=False)
    valid_qsos = Column(Integer, default=0, nullable=False)
    duplicate_qsos = Column(Integer, default=0, nullable=False)
    invalid_qsos = Column(Integer, default=0, nullable=False)
    not_in_log_qsos = Column(Integer, default=0, nullable=False)

    # Scoring
    total_points = Column(Integer, default=0, nullable=False)
    multipliers = Column(Integer, default=0, nullable=False)
    final_score = Column(Integer, default=0, nullable=False)

    # Detailed Breakdowns (stored as JSON)
    points_by_band = Column(JSON)  # {"10m": 1000, "20m": 500}
    points_by_mode = Column(JSON)  # {"CW": 800, "SSB": 700}
    points_by_type = Column(JSON)  # {"same_country": 200, "different_country": 1500}
    qsos_by_band = Column(JSON)  # {"10m": 50, "20m": 30}
    qsos_by_mode = Column(JSON)  # {"CW": 40, "SSB": 40}
    qsos_by_hour = Column(JSON)  # {"12": 10, "13": 15, ...}

    # Multipliers Detail
    multipliers_list = Column(JSON)  # ["BA", "CF", "CO", "W", "K", ...]
    multipliers_by_band = Column(JSON)  # If per-band multipliers
    multipliers_by_mode = Column(JSON)  # If per-mode multipliers

    # Validation Stats
    validation_errors = Column(JSON)  # List of validation errors with counts

    # Rank (can be populated after all logs are scored)
    rank_overall = Column(Integer)
    rank_category = Column(Integer)
    rank_country = Column(Integer)

    # Calculation metadata
    calculated_at = Column(DateTime, nullable=False)
    calculation_version = Column(String(20))  # Version of scoring algorithm
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    log = relationship("Log", back_populates="score")

    # Indexes
    __table_args__ = (
        Index("idx_score_final_score", "final_score"),
        Index("idx_score_log_id", "log_id"),
    )

    def __repr__(self):
        return (f"<Score(id={self.id}, log_id={self.log_id}, "
                f"final_score={self.final_score})>")


class CTYData(Base):
    """
    Country/prefix data from cty.dat file
    Used for callsign prefix lookup and DXCC entity identification
    """
    __tablename__ = "cty_data"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Primary DXCC entity information
    country_name = Column(String(100), nullable=False)  # Argentina
    dxcc_code = Column(Integer, nullable=True)  # DXCC entity number (ADIF code, may not be present for all)
    continent = Column(String(2), nullable=False)  # SA, NA, EU, AS, AF, OC
    itu_zone = Column(Integer, nullable=False)
    cq_zone = Column(Integer, nullable=False)

    # Timezone and geographic info
    timezone_offset = Column(Float)  # UTC offset in hours
    latitude = Column(Float)
    longitude = Column(Float)

    # Primary prefix (main prefix for the entity)
    primary_prefix = Column(String(10), nullable=False)  # LU, W, JA, etc.

    # All prefixes (JSON array of all possible prefixes for this entity)
    # Includes primary prefix plus all possible variants
    prefixes = Column(JSON, nullable=False)  # ["LU", "AY", "AZ", "L2", "L3", ...]

    # Special handling for contest exchanges
    # Some entities might have special province/state codes
    exchange_zones = Column(JSON)  # For contests that use zones as exchange

    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    cty_file_date = Column(String(20))  # Date from cty.dat file
    is_active = Column(Boolean, default=True)

    # Indexes for fast prefix lookups
    __table_args__ = (
        Index("idx_cty_dxcc_code", "dxcc_code"),
        Index("idx_cty_continent", "continent"),
        Index("idx_cty_primary_prefix", "primary_prefix"),
        Index("idx_cty_cq_zone", "cq_zone"),
    )

    def __repr__(self):
        return f"<CTYData(dxcc={self.dxcc_code}, country='{self.country_name}', prefix='{self.primary_prefix}')>"


class AuditLog(Base):
    """
    Audit trail for important operations
    Tracks changes to logs, scores, and validations
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # Log, Contact, Score
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # INSERT, UPDATE, DELETE, VALIDATE, SCORE
    user = Column(String(100))  # Who performed the action
    changes = Column(JSON)  # What changed
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_timestamp", "timestamp"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity='{self.entity_type}')>"

