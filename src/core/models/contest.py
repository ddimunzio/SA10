"""
Core data models for contest entities using Pydantic.
These models represent the domain entities independent of storage.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BandEnum(str, Enum):
    """Amateur radio bands."""
    BAND_160M = "160m"
    BAND_80M = "80m"
    BAND_40M = "40m"
    BAND_20M = "20m"
    BAND_15M = "15m"
    BAND_10M = "10m"
    BAND_6M = "6m"
    BAND_2M = "2m"


class ModeEnum(str, Enum):
    """Operating modes."""
    CW = "CW"
    SSB = "SSB"
    FM = "FM"
    RTTY = "RTTY"
    PSK = "PSK"
    FT8 = "FT8"
    FT4 = "FT4"


class Contact(BaseModel):
    """Represents a single QSO (contact) in a contest log."""

    timestamp: datetime = Field(..., description="UTC timestamp of the contact")
    frequency: int = Field(..., description="Frequency in kHz", gt=0)
    mode: ModeEnum = Field(..., description="Operating mode")
    callsign: str = Field(..., description="Contacted station callsign")

    # Exchange sent
    rst_sent: str = Field(..., description="Signal report sent")
    exchange_sent: str = Field(..., description="Exchange information sent")

    # Exchange received
    rst_received: str = Field(..., description="Signal report received")
    exchange_received: str = Field(..., description="Exchange information received")

    # Computed/validation fields
    band: Optional[BandEnum] = Field(None, description="Band derived from frequency")
    points: Optional[int] = Field(0, description="Points for this contact")
    is_multiplier: bool = Field(False, description="Whether this contact is a multiplier")
    is_duplicate: bool = Field(False, description="Whether this is a duplicate contact")
    is_valid: bool = Field(True, description="Whether this contact is valid")
    validation_notes: Optional[str] = Field(None, description="Validation error notes")

    @field_validator('callsign')
    @classmethod
    def validate_callsign(cls, v: str) -> str:
        """Validate and normalize callsign."""
        return v.upper().strip()

    @field_validator('rst_sent', 'rst_received')
    @classmethod
    def validate_rst(cls, v: str) -> str:
        """Validate RS/RST format (2 digits for SSB, 3 digits for CW)."""
        v = v.strip()
        if not v.isdigit():
            raise ValueError("RS/RST must contain only digits")
        if len(v) not in [2, 3]:
            raise ValueError("RS must be 2 digits (SSB) or RST must be 3 digits (CW)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2025-11-13T14:30:00Z",
                "frequency": 28500,
                "mode": "SSB",
                "callsign": "LU1ABC",
                "rst_sent": "59",
                "exchange_sent": "13",
                "rst_received": "59",
                "exchange_received": "11",
                "band": "10m",
                "points": 2,
                "is_multiplier": True,
                "is_duplicate": False,
                "is_valid": True
            }
        }
    )


class Station(BaseModel):
    """Represents the station information."""

    callsign: str = Field(..., description="Operator callsign")
    category: Optional[str] = Field(None, description="Contest category")
    power: Optional[str] = Field(None, description="Power level (HIGH/LOW/QRP)")
    location: Optional[str] = Field(None, description="Operating location (province/state)")
    operators: Optional[List[str]] = Field(default_factory=list, description="List of operators")

    @field_validator('callsign')
    @classmethod
    def validate_callsign(cls, v: str) -> str:
        """Validate and normalize callsign."""
        return v.upper().strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "callsign": "LU1ABC",
                "category": "SOAB",
                "power": "HIGH",
                "location": "13",
                "operators": ["LU1ABC"]
            }
        }
    )


class ContestLog(BaseModel):
    """Represents a complete contest log submission."""

    station: Station = Field(..., description="Station information")
    contacts: List[Contact] = Field(default_factory=list, description="List of contacts")

    # Metadata
    contest_name: str = Field(..., description="Contest identifier")
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")

    @property
    def total_qsos(self) -> int:
        """Total number of QSOs."""
        return len(self.contacts)

    @property
    def valid_qsos(self) -> int:
        """Number of valid QSOs."""
        return sum(1 for c in self.contacts if c.is_valid and not c.is_duplicate)

    @property
    def duplicate_qsos(self) -> int:
        """Number of duplicate QSOs."""
        return sum(1 for c in self.contacts if c.is_duplicate)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "station": {
                    "callsign": "LU1ABC",
                    "category": "SOAB",
                    "power": "HIGH",
                    "location": "13"
                },
                "contest_name": "sa10m",
                "contacts": []
            }
        }
    )


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown."""

    total_qsos: int = Field(0, description="Total contacts")
    valid_qsos: int = Field(0, description="Valid contacts")
    duplicate_qsos: int = Field(0, description="Duplicate contacts")
    invalid_qsos: int = Field(0, description="Invalid contacts")

    total_points: int = Field(0, description="Total points before multipliers")
    multipliers: int = Field(0, description="Number of multipliers")
    final_score: int = Field(0, description="Final score (points × multipliers)")

    # Per-band/mode breakdown
    qsos_by_band: dict = Field(default_factory=dict, description="QSOs per band")
    qsos_by_mode: dict = Field(default_factory=dict, description="QSOs per mode")
    points_by_band: dict = Field(default_factory=dict, description="Points per band")
    points_by_mode: dict = Field(default_factory=dict, description="Points per mode")

    multipliers_worked: List[str] = Field(default_factory=list, description="List of multipliers")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_qsos": 150,
                "valid_qsos": 145,
                "duplicate_qsos": 5,
                "invalid_qsos": 0,
                "total_points": 350,
                "multipliers": 23,
                "final_score": 8050,
                "qsos_by_band": {"10m": 150},
                "qsos_by_mode": {"SSB": 100, "CW": 50},
                "multipliers_worked": ["11", "12", "13", "14", "15", "..."]
            }
        }
    )


class ContestDefinition(BaseModel):
    """Represents a contest rule definition loaded from YAML."""

    name: str = Field(..., description="Contest name")
    slug: str = Field(..., description="Contest identifier")
    description: Optional[str] = Field(None, description="Contest description")
    website: Optional[str] = Field(None, description="Contest website")

    bands: List[str] = Field(..., description="Allowed bands")
    modes: List[str] = Field(..., description="Allowed modes")
    duration_hours: int = Field(..., description="Contest duration")

    # This will be expanded as we implement the rules engine
    rules_data: dict = Field(default_factory=dict, description="Raw rules configuration")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "SA10M Contest",
                "slug": "sa10m",
                "description": "10 meter Argentine Provinces Contest",
                "website": "https://sa10m.com.ar",
                "bands": ["10m"],
                "modes": ["SSB", "CW"],
                "duration_hours": 24
            }
        }
    )

