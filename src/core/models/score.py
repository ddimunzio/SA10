"""
Pydantic models for Score data

Represents calculated scores and breakdowns.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, ConfigDict, Field


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    # QSO counts
    total_qsos: int = Field(0, description="Total QSOs in log")
    valid_qsos: int = Field(0, description="Valid QSOs")
    duplicate_qsos: int = Field(0, description="Duplicate QSOs")
    invalid_qsos: int = Field(0, description="Invalid QSOs")
    not_in_log_qsos: int = Field(0, description="Not-in-log QSOs")

    # Points
    total_points: int = Field(0, description="Total points")

    # Points by category
    points_by_band: Dict[str, int] = Field(default_factory=dict, description="Points per band")
    points_by_mode: Dict[str, int] = Field(default_factory=dict, description="Points per mode")
    points_by_type: Dict[str, int] = Field(default_factory=dict, description="Points by contact type")

    # QSO counts by category
    qsos_by_band: Dict[str, int] = Field(default_factory=dict, description="QSOs per band")
    qsos_by_mode: Dict[str, int] = Field(default_factory=dict, description="QSOs per mode")
    qsos_by_hour: Dict[str, int] = Field(default_factory=dict, description="QSOs per hour")

    # Multipliers
    total_multipliers: int = Field(0, description="Total multipliers")
    multipliers_list: List[str] = Field(default_factory=list, description="List of worked multipliers")
    multipliers_by_band: Optional[Dict[str, List[str]]] = Field(None, description="Multipliers per band")
    multipliers_by_mode: Optional[Dict[str, List[str]]] = Field(None, description="Multipliers per mode")

    # Final score
    final_score: int = Field(0, description="Final calculated score")

    # Validation errors
    validation_errors: Optional[Dict[str, int]] = Field(None, description="Validation error counts")

    model_config = ConfigDict(from_attributes=True)


class Score(ScoreBreakdown):
    """Complete score model with system fields"""
    id: Optional[int] = None
    log_id: int

    # Rankings
    rank_overall: Optional[int] = None
    rank_category: Optional[int] = None
    rank_country: Optional[int] = None

    # Calculation metadata
    calculated_at: datetime
    calculation_version: Optional[str] = None
    notes: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScoreCreate(BaseModel):
    """Model for creating a new score"""
    log_id: int

    total_qsos: int = 0
    valid_qsos: int = 0
    duplicate_qsos: int = 0
    invalid_qsos: int = 0
    not_in_log_qsos: int = 0

    total_points: int = 0
    multipliers: int = 0
    final_score: int = 0

    points_by_band: Optional[Dict[str, int]] = None
    points_by_mode: Optional[Dict[str, int]] = None
    points_by_type: Optional[Dict[str, int]] = None
    qsos_by_band: Optional[Dict[str, int]] = None
    qsos_by_mode: Optional[Dict[str, int]] = None
    qsos_by_hour: Optional[Dict[str, int]] = None

    multipliers_list: Optional[List[str]] = None
    multipliers_by_band: Optional[Dict[str, List[str]]] = None
    multipliers_by_mode: Optional[Dict[str, List[str]]] = None

    validation_errors: Optional[Dict[str, int]] = None

    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    calculation_version: Optional[str] = None
    notes: Optional[str] = None


class ScoreUpdate(BaseModel):
    """Model for updating a score"""
    rank_overall: Optional[int] = None
    rank_category: Optional[int] = None
    rank_country: Optional[int] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScoreSummary(BaseModel):
    """
    Simplified score summary for display
    """
    log_id: int
    callsign: str

    total_qsos: int
    valid_qsos: int
    duplicate_qsos: int

    total_points: int
    multipliers: int
    final_score: int

    rank_overall: Optional[int] = None
    rank_category: Optional[int] = None

    # Category for grouping
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntry(BaseModel):
    """
    Leaderboard entry with station and score information
    """
    rank: int
    callsign: str
    name: Optional[str] = None
    country: Optional[str] = None

    category_operator: Optional[str] = None
    category_band: Optional[str] = None
    category_mode: Optional[str] = None
    category_power: Optional[str] = None

    qsos: int
    multipliers: int
    score: int

    model_config = ConfigDict(from_attributes=True)

