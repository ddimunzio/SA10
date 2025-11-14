"""
Tests for core contest models.
"""

import pytest
from datetime import datetime
from src.core.models.contest import (
    Contact, Station, ContestLog, ScoreBreakdown,
    BandEnum, ModeEnum
)


def test_contact_creation():
    """Test creating a valid contact."""
    contact = Contact(
        timestamp=datetime(2025, 11, 13, 14, 30, 0),
        frequency=28500,
        mode=ModeEnum.SSB,
        callsign="LU1ABC",
        rst_sent="59",
        exchange_sent="13",
        rst_received="59",
        exchange_received="11",
        band=BandEnum.BAND_10M
    )

    assert contact.callsign == "LU1ABC"
    assert contact.mode == ModeEnum.SSB
    assert contact.frequency == 28500


def test_callsign_normalization():
    """Test that callsigns are normalized to uppercase."""
    contact = Contact(
        timestamp=datetime(2025, 11, 13, 14, 30, 0),
        frequency=28500,
        mode=ModeEnum.SSB,
        callsign="lu1abc",  # lowercase
        rst_sent="59",
        exchange_sent="13",
        rst_received="59",
        exchange_received="11"
    )

    assert contact.callsign == "LU1ABC"


def test_invalid_rst():
    """Test that invalid RST raises error."""
    with pytest.raises(ValueError):
        Contact(
            timestamp=datetime(2025, 11, 13, 14, 30, 0),
            frequency=28500,
            mode=ModeEnum.SSB,
            callsign="LU1ABC",
            rst_sent="5",  # Only 1 digit, invalid
            exchange_sent="13",
            rst_received="59",
            exchange_received="11"
        )


def test_station_creation():
    """Test creating a station."""
    station = Station(
        callsign="LU1ABC",
        category="SOAB",
        power="HIGH",
        location="13"
    )

    assert station.callsign == "LU1ABC"
    assert station.category == "SOAB"

    assert station.callsign == "LU1ABC"
    assert station.category == "SOAB"


def test_contest_log():
    """Test creating a contest log."""
    station = Station(
        callsign="LU1ABC",
        category="SOAB",
        power="HIGH",
        location="13"
    )

    log = ContestLog(
        station=station,
        contest_name="sa10m",
        contacts=[]
    )

    assert log.station.callsign == "LU1ABC"
    assert log.total_qsos == 0


def test_contest_log_with_contacts():
    """Test contest log with multiple contacts."""
    station = Station(callsign="LU1ABC", location="13")

    contacts = [
        Contact(
            timestamp=datetime(2025, 11, 13, 14, 30, 0),
            frequency=28500,
            mode=ModeEnum.SSB,
            callsign="LU2XYZ",
            rst_sent="59",
            exchange_sent="13",
            rst_received="59",
            exchange_received="11",
            is_valid=True
        ),
        Contact(
            timestamp=datetime(2025, 11, 13, 14, 35, 0),
            frequency=28500,
            mode=ModeEnum.CW,
            callsign="LU3ABC",
            rst_sent="599",
            exchange_sent="13",
            rst_received="599",
            exchange_received="12",
            is_valid=True
        )
    ]

    log = ContestLog(
        station=station,
        contest_name="sa10m",
        contacts=contacts
    )

    assert log.total_qsos == 2
    assert log.valid_qsos == 2
    assert log.duplicate_qsos == 0


def test_score_breakdown():
    """Test score breakdown model."""
    score = ScoreBreakdown(
        total_qsos=150,
        valid_qsos=145,
        duplicate_qsos=5,
        total_points=350,
        multipliers=23,
        final_score=8050,
        multipliers_worked=["11", "12", "13"]
    )

    assert score.final_score == 8050
    assert score.multipliers == 23
    assert len(score.multipliers_worked) == 3


def test_rs_validation_ssb():
    """Test that 2-digit RS is valid for SSB."""
    contact = Contact(
        timestamp=datetime(2025, 11, 13, 14, 30, 0),
        frequency=28500,
        mode=ModeEnum.SSB,
        callsign="LU1ABC",
        rst_sent="59",  # 2 digits - valid for SSB
        exchange_sent="13",
        rst_received="59",
        exchange_received="11"
    )
    assert contact.rst_sent == "59"
    assert contact.rst_received == "59"


def test_rst_validation_cw():
    """Test that 3-digit RST is valid for CW."""
    contact = Contact(
        timestamp=datetime(2025, 11, 13, 14, 30, 0),
        frequency=28500,
        mode=ModeEnum.CW,
        callsign="LU1ABC",
        rst_sent="599",  # 3 digits - valid for CW
        exchange_sent="13",
        rst_received="599",
        exchange_received="11"
    )
    assert contact.rst_sent == "599"
    assert contact.rst_received == "599"


def test_invalid_rst_four_digits():
    """Test that 4-digit RST is invalid."""
    with pytest.raises(ValueError):
        Contact(
            timestamp=datetime(2025, 11, 13, 14, 30, 0),
            frequency=28500,
            mode=ModeEnum.CW,
            callsign="LU1ABC",
            rst_sent="5999",  # 4 digits - invalid
            exchange_sent="13",
            rst_received="599",
            exchange_received="11"
        )


