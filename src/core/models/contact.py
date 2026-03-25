"""
Pydantic models for Contact/QSO data validation

These models ensure data integrity when parsing Cabrillo logs
and provide type safety throughout the application.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class Mode(str, Enum):
    """Valid contest modes"""
    CW = "CW"
    PH = "PH"  # Phone (SSB)
    SSB = "SSB"  # Alias for PH
    FM = "FM"
    RY = "RY"  # RTTY
    DG = "DG"  # Digital


class Band(str, Enum):
    """Valid amateur radio bands"""
    BAND_160M = "160m"
    BAND_80M = "80m"
    BAND_40M = "40m"
    BAND_20M = "20m"
    BAND_15M = "15m"
    BAND_10M = "10m"
    BAND_6M = "6m"
    BAND_2M = "2m"
    BAND_70CM = "70cm"


class ValidationStatusEnum(str, Enum):
    """QSO validation status"""
    VALID = "valid"
    DUPLICATE = "duplicate"
    INVALID_CALLSIGN = "invalid_callsign"
    INVALID_EXCHANGE = "invalid_exchange"
    OUT_OF_PERIOD = "out_of_period"
    INVALID_BAND = "invalid_band"
    INVALID_MODE = "invalid_mode"
    NOT_IN_LOG = "not_in_log"
    TIME_MISMATCH = "time_mismatch"
    EXCHANGE_MISMATCH = "exchange_mismatch"


class ContactBase(BaseModel):
    """Base contact model with common fields"""
    frequency: int = Field(..., description="Frequency in kHz", ge=1800, le=250000)
    mode: str = Field(..., description="Operating mode (CW, PH, etc.)")
    qso_date: str = Field(..., description="QSO date in YYYY-MM-DD format", pattern=r'^\d{4}-\d{2}-\d{2}$')
    qso_time: str = Field(..., description="QSO time in HHMM UTC format", pattern=r'^\d{4}$')

    call_sent: str = Field(..., description="Callsign sent", min_length=3, max_length=20)
    rst_sent: str = Field(..., description="Signal report sent", min_length=1, max_length=10)
    exchange_sent: str = Field(..., description="Exchange data sent", max_length=50)

    call_received: str = Field(..., description="Callsign received", min_length=3, max_length=20)
    rst_received: str = Field(..., description="Signal report received", min_length=0, max_length=10)  # Allow empty for missing data
    exchange_received: str = Field(..., description="Exchange data received", min_length=0, max_length=50)  # Allow empty for missing data

    transmitter_id: Optional[str] = Field(None, description="Transmitter ID for multi-transmitter", max_length=5)

    @validator('mode')
    def validate_mode(cls, v):
        """Normalize and validate mode"""
        v = v.upper()
        # Accept both PH and SSB
        if v == 'SSB':
            v = 'PH'
        if v not in ['CW', 'PH', 'FM', 'RY', 'DG']:
            raise ValueError(f'Invalid mode: {v}')
        return v

    @validator('call_sent', 'call_received')
    def validate_callsign(cls, v):
        """Basic callsign validation - lenient to allow import of invalid calls"""
        v = v.upper().strip()
        if not v:
            raise ValueError('Callsign cannot be empty')
        # Allow alphanumeric callsigns plus / and - for special callsigns
        # Validation of proper format happens later during scoring
        # This allows us to import logs with potentially invalid callsigns
        # They will be marked as invalid during the validation phase
        if not v.replace('/', '').replace('-', '').isalnum():
            raise ValueError(f'Callsign contains invalid characters: {v}')
        return v

    @validator('frequency')
    def validate_frequency(cls, v):
        """Validate frequency is within amateur bands"""
        # Add basic frequency validation
        if v < 1800:
            raise ValueError('Frequency must be at least 1800 kHz')
        return v

    class Config:
        use_enum_values = True


class Contact(ContactBase):
    """Complete contact model with derived fields"""
    id: Optional[int] = None
    log_id: int

    qso_datetime: datetime
    band: Optional[str] = None

    points: int = 0
    is_multiplier: bool = False
    multiplier_type: Optional[str] = None
    multiplier_value: Optional[str] = None

    is_valid: bool = True
    is_duplicate: bool = False
    duplicate_of_id: Optional[int] = None
    validation_status: ValidationStatusEnum = ValidationStatusEnum.VALID
    validation_notes: Optional[str] = None

    matched_contact_id: Optional[int] = None
    time_diff_seconds: Optional[int] = None
    frequency_diff_khz: Optional[int] = None

    metadata: Optional[Dict[str, Any]] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ContactCreate(ContactBase):
    """Model for creating a new contact"""
    log_id: int

    @root_validator(skip_on_failure=True)
    def compute_datetime(cls, values):
        """Compute the combined datetime from date and time"""
        qso_date = values.get('qso_date')
        qso_time = values.get('qso_time')

        if qso_date and qso_time:
            # Parse date and time
            date_str = f"{qso_date} {qso_time[:2]}:{qso_time[2:4]}"
            values['qso_datetime'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M')

        return values


    @root_validator(skip_on_failure=True)
    def compute_band(cls, values):
        """Derive band from frequency"""
        freq = values.get('frequency')
        if freq:
            values['band'] = frequency_to_band(freq)
        return values


class ContactUpdate(BaseModel):
    """Model for updating a contact"""
    points: Optional[int] = None
    is_multiplier: Optional[bool] = None
    multiplier_type: Optional[str] = None
    multiplier_value: Optional[str] = None

    is_valid: Optional[bool] = None
    is_duplicate: Optional[bool] = None
    duplicate_of_id: Optional[int] = None
    validation_status: Optional[ValidationStatusEnum] = None
    validation_notes: Optional[str] = None

    matched_contact_id: Optional[int] = None
    time_diff_seconds: Optional[int] = None
    frequency_diff_khz: Optional[int] = None

    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


def frequency_to_band(frequency_khz: int) -> str:
    """
    Convert frequency in kHz to band designation

    Args:
        frequency_khz: Frequency in kilohertz

    Returns:
        Band designation (e.g., "10m", "20m")
    """
    if 1800 <= frequency_khz < 2000:
        return "160m"
    elif 3500 <= frequency_khz < 4000:
        return "80m"
    elif 7000 <= frequency_khz < 7300:
        return "40m"
    elif 10100 <= frequency_khz < 10150:
        return "30m"
    elif 14000 <= frequency_khz < 14350:
        return "20m"
    elif 18068 <= frequency_khz < 18168:
        return "17m"
    elif 21000 <= frequency_khz < 21450:
        return "15m"
    elif 24890 <= frequency_khz < 24990:
        return "12m"
    elif 28000 <= frequency_khz < 29700:
        return "10m"
    elif 50000 <= frequency_khz < 54000:
        return "6m"
    elif 144000 <= frequency_khz < 148000:
        return "2m"
    elif 420000 <= frequency_khz < 450000:
        return "70cm"
    else:
        return "UNKNOWN"

