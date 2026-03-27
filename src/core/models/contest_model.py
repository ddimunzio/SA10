"""
Pydantic models for Contest data

Represents contest definitions and metadata.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContestBase(BaseModel):
    """Base contest model"""
    name: str = Field(..., description="Contest name", min_length=3, max_length=100)
    slug: str = Field(..., description="URL-friendly slug", min_length=2, max_length=50)
    start_date: datetime = Field(..., description="Contest start date/time")
    end_date: datetime = Field(..., description="Contest end date/time")
    rules_file: str = Field(..., description="Path to YAML rules file", max_length=200)

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        """Ensure slug is lowercase and alphanumeric with dashes"""
        v = v.lower().strip()
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only letters, numbers, dashes, and underscores')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Ensure end date is after start date"""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v

    model_config = ConfigDict(use_enum_values=True)


class Contest(ContestBase):
    """Complete contest model with system fields"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ContestCreate(ContestBase):
    """Model for creating a new contest"""
    pass


class ContestUpdate(BaseModel):
    """Model for updating a contest"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    rules_file: Optional[str] = Field(None, max_length=200)

    model_config = ConfigDict(from_attributes=True)


class ContestSummary(BaseModel):
    """
    Simplified contest summary for display
    """
    id: int
    name: str
    slug: str
    start_date: datetime
    end_date: datetime
    total_logs: int = 0

    model_config = ConfigDict(from_attributes=True)

