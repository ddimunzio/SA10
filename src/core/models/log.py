"""
Pydantic models for Station/Log data

Represents the header information from Cabrillo log files.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr


class LogBase(BaseModel):
    """Base log/station model with Cabrillo header fields"""
    # Required fields
    callsign: str = Field(..., description="Station callsign", min_length=3, max_length=20)
    contest_name: str = Field(..., description="Contest name from CONTEST field")

    # Cabrillo version
    cabrillo_version: str = Field(default="3.0", description="Cabrillo format version")

    # Location and club
    location: Optional[str] = Field(None, description="Location code (DX, SA, etc.)", max_length=50)
    club: Optional[str] = Field(None, description="Club affiliation", max_length=100)

    # Category fields
    category_operator: Optional[str] = Field(None, description="Operator category", max_length=50)
    category_assisted: Optional[str] = Field(None, description="Assisted category", max_length=50)
    category_band: Optional[str] = Field(None, description="Band category", max_length=20)
    category_mode: Optional[str] = Field(None, description="Mode category", max_length=20)
    category_power: Optional[str] = Field(None, description="Power category", max_length=20)
    category_station: Optional[str] = Field(None, description="Station category", max_length=50)
    category_transmitter: Optional[str] = Field(None, description="Transmitter category", max_length=20)
    category_overlay: Optional[str] = Field(None, description="Overlay category", max_length=50)
    category_time: Optional[str] = Field(None, description="Time category", max_length=20)

    # Operator information
    operators: Optional[str] = Field(None, description="Comma-separated operator callsigns")
    name: Optional[str] = Field(None, description="Operator name", max_length=200)

    # Address information
    address: Optional[str] = Field(None, description="Full street address")
    address_city: Optional[str] = Field(None, description="City", max_length=100)
    address_state_province: Optional[str] = Field(None, description="State/Province", max_length=100)
    address_postalcode: Optional[str] = Field(None, description="Postal code", max_length=20)
    address_country: Optional[str] = Field(None, description="Country", max_length=100)

    # Grid locator
    grid_locator: Optional[str] = Field(None, description="Maidenhead grid locator", max_length=10)

    # Contact information
    email: Optional[EmailStr] = Field(None, description="Email address")

    # Score claim
    claimed_score: Optional[int] = Field(None, description="Claimed score", ge=0)

    # Software information
    created_by: Optional[str] = Field(None, description="Logging software used", max_length=200)

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional Cabrillo fields")

    @field_validator('callsign')
    @classmethod
    def validate_callsign(cls, v):
        """Validate and normalize callsign"""
        v = v.upper().strip()
        if not v:
            raise ValueError('Callsign cannot be empty')
        return v

    @field_validator('category_operator', 'category_assisted', 'category_band', 'category_mode',
               'category_power', 'category_station', 'category_transmitter', 'category_overlay')
    @classmethod
    def normalize_category(cls, v):
        """Normalize category fields to uppercase"""
        return v.upper() if v else None

    model_config = ConfigDict(use_enum_values=True)


class Log(LogBase):
    """Complete log model with system fields"""
    id: Optional[int] = None
    contest_id: int

    # File information
    file_path: Optional[str] = None
    file_hash: Optional[str] = None

    # Processing status
    status: str = "pending"
    validation_notes: Optional[str] = None
    processed_at: Optional[datetime] = None

    # Timestamps
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LogCreate(LogBase):
    """Model for creating a new log"""
    contest_id: int
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    submitted_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class LogUpdate(BaseModel):
    """Model for updating a log"""
    status: Optional[str] = None
    validation_notes: Optional[str] = None
    processed_at: Optional[datetime] = None

    # Allow updating categories if needed
    category_operator: Optional[str] = None
    category_assisted: Optional[str] = None
    category_band: Optional[str] = None
    category_mode: Optional[str] = None
    category_power: Optional[str] = None

    claimed_score: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class StationInfo(BaseModel):
    """
    Station information extracted from log
    Used for display and reporting
    """
    callsign: str
    operators: Optional[List[str]] = None
    location: Optional[str] = None
    club: Optional[str] = None
    grid_locator: Optional[str] = None

    # Categories
    category_operator: Optional[str] = None
    category_band: Optional[str] = None
    category_mode: Optional[str] = None
    category_power: Optional[str] = None
    category_station: Optional[str] = None

    # Address
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None

    @field_validator('operators', mode='before')
    @classmethod
    def parse_operators(cls, v):
        """Parse comma-separated operators into list"""
        if isinstance(v, str):
            return [op.strip() for op in v.split(',') if op.strip()]
        return v

    model_config = ConfigDict(from_attributes=True)

