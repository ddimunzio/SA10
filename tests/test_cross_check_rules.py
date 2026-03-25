"""
Test Cases for Cross-Check Rules

Tests the three detection types:
1. NIL (Not-in-Log) - Station submitted but has no record
2. UNIQUE - Station didn't submit a log
3. BUSTED - Transcription error with reciprocal QSO evidence

Based on docs/CROSSCHECK_DETECTION_FLOW.md
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, Contest, Log, Contact as DBContact
from src.services.cross_check_service import CrossCheckService, UBNType


def Contact(**kwargs):
    """Helper to create Contact with derived fields"""
    if 'qso_datetime' in kwargs:
        dt = kwargs['qso_datetime']
        if 'qso_date' not in kwargs:
            kwargs['qso_date'] = dt.strftime('%Y-%m-%d')
        if 'qso_time' not in kwargs:
            kwargs['qso_time'] = dt.strftime('%H%M')
    
    # Ensure call_sent is present (required by DB model)
    if 'call_sent' not in kwargs:
        kwargs['call_sent'] = "TEST_STATION"

    return DBContact(**kwargs)


@pytest.fixture
def db_session():
    """Create in-memory database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def test_contest(db_session):
    """Create a test contest"""
    contest = Contest(
        name="Test Contest 2025",
        slug="test-2025",
        start_date=datetime(2025, 3, 8, 0, 0, 0),
        end_date=datetime(2025, 3, 9, 23, 59, 59),
        rules_file="config/contests/SA10MC.txt"
    )
    db_session.add(contest)
    db_session.commit()
    return contest


class TestNILDetection:
    """Test Not-in-Log (NIL) detection"""

    def test_nil_basic(self, db_session, test_contest):
        """
        Case: Both stations submitted, but one has no record

        LW5HR logs LU6DX
        LU6DX submitted but has no record of LW5HR

        Expected: NIL
        """
        # Create logs
        log_lw5hr = Log(
            contest_id=test_contest.id,
            callsign="LW5HR",
            operators="LW5HR"
        )
        log_lu6dx = Log(
            contest_id=test_contest.id,
            callsign="LU6DX",
            operators="LU6DX"
        )
        db_session.add_all([log_lw5hr, log_lu6dx])
        db_session.commit()

        # LW5HR logs contact with LU6DX
        contact = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 0),
            call_received="LU6DX",
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59",
            rst_received="59",
            exchange_sent="13",
            exchange_received="14",
            is_valid=True
        )
        db_session.add(contact)
        db_session.commit()

        # Run cross-check
        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Verify NIL detected
        assert log_lw5hr.id in ubn_by_log
        nil_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.NOT_IN_LOG]
        assert len(nil_entries) == 1
        assert nil_entries[0].worked_callsign == "LU6DX"

    def test_nil_with_reciprocal_time_outside_tolerance(self, db_session, test_contest):
        """
        Case: Both stations have QSO but times don't match (>1 minute)

        LW5HR logs LU6DX at 14:23
        LU6DX logs LW5HR at 14:30 (7 minutes later)

        Expected: NIL (time difference too large)
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_lu6dx = Log(contest_id=test_contest.id, callsign="LU6DX", operators="LU6DX")
        db_session.add_all([log_lw5hr, log_lu6dx])
        db_session.commit()

        # LW5HR logs at 14:23
        contact1 = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 0),
            call_received="LU6DX",
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="13", exchange_received="14",
            is_valid=True
        )

        # LU6DX logs at 14:30 (7 minutes later)
        contact2 = Contact(
            log_id=log_lu6dx.id,
            qso_datetime=datetime(2025, 3, 8, 14, 30, 0),
            call_received="LW5HR",
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="14", exchange_received="13",
            is_valid=True
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        # Run cross-check
        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Both should have NIL
        assert log_lw5hr.id in ubn_by_log
        assert log_lu6dx.id in ubn_by_log


class TestUNIQUEDetection:
    """Test UNIQUE call detection"""

    def test_unique_basic(self, db_session, test_contest):
        """
        Case: Worked station didn't submit

        LW5HR logs K9XYZ
        K9XYZ did not submit a log

        Expected: UNIQUE
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        db_session.add(log_lw5hr)
        db_session.commit()

        contact = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 16, 45, 0),
            call_received="K9XYZ",
            band="21MHz",
            mode="SSB",
            frequency=21300,
            rst_sent="59", rst_received="59",
            exchange_sent="13", exchange_received="04",
            is_valid=True
        )
        db_session.add(contact)
        db_session.commit()

        # Run cross-check
        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Verify UNIQUE detected
        assert log_lw5hr.id in ubn_by_log
        unique_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.UNIQUE]
        assert len(unique_entries) == 1
        assert unique_entries[0].worked_callsign == "K9XYZ"

    def test_unique_similar_call_no_reciprocal(self, db_session, test_contest):
        """
        Case: Similar call exists but no reciprocal QSO

        LW5HR logs LU6DX
        LU5DX submitted but has no LW5HR in log
        LU6DX did not submit

        Expected: UNIQUE (not BUSTED, no reciprocal QSO)
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_lu5dx = Log(contest_id=test_contest.id, callsign="LU5DX", operators="LU5DX")
        db_session.add_all([log_lw5hr, log_lu5dx])
        db_session.commit()

        # LW5HR logs LU6DX (typo? or legitimate?)
        contact = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 15, 30, 0),
            call_received="LU6DX",
            band="14MHz",
            mode="CW",
            frequency=14050,
            rst_sent="599", rst_received="599",
            exchange_sent="13", exchange_received="14",
            is_valid=True
        )
        db_session.add(contact)
        db_session.commit()

        # Run cross-check
        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Should be UNIQUE, NOT BUSTED (no reciprocal QSO)
        unique_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.UNIQUE]
        busted_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.BUSTED]

        assert len(unique_entries) == 1
        assert unique_entries[0].worked_callsign == "LU6DX"
        assert len(busted_entries) == 0  # NOT busted!


class TestBUSTEDDetection:
    """Test BUSTED call detection"""

    def test_busted_with_reciprocal(self, db_session, test_contest):
        """
        Case: Typo with reciprocal QSO evidence

        LW5HR logs LU6DX (typo)
        LU5DX submitted and HAS LW5HR logged at same time

        Expected: BUSTED (LU6DX should be LU5DX)
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_lu5dx = Log(contest_id=test_contest.id, callsign="LU5DX", operators="LU5DX")
        db_session.add_all([log_lw5hr, log_lu5dx])
        db_session.commit()

        # LW5HR logs LU6DX (typo)
        contact1 = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 0),
            call_received="LU6DX",  # Wrong!
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="13", exchange_received="14",
            is_valid=True
        )

        # LU5DX logs LW5HR correctly (reciprocal)
        contact2 = Contact(
            log_id=log_lu5dx.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 15),  # Within 1 minute
            call_received="LW5HR",
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="14", exchange_received="13",
            is_valid=True
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        # Run cross-check
        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Verify BUSTED detected
        assert log_lw5hr.id in ubn_by_log
        busted_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.BUSTED]
        assert len(busted_entries) == 1
        assert busted_entries[0].worked_callsign == "LU6DX"
        assert busted_entries[0].suggested_call == "LU5DX"
        assert busted_entries[0].other_station_has_qso is True

    def test_busted_levenshtein_distance_1(self, db_session, test_contest):
        """
        Case: Single character difference with reciprocal

        LW5HR logs W1XZZ
        W1XZZ doesn't exist
        W1ZZZ submitted and has LW5HR logged

        Expected: BUSTED (W1XZZ should be W1ZZZ)
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_w1zzz = Log(contest_id=test_contest.id, callsign="W1ZZZ", operators="W1ZZZ")
        db_session.add_all([log_lw5hr, log_w1zzz])
        db_session.commit()

        contact1 = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 18, 34, 0),
            call_received="W1XZZ",  # Should be W1ZZZ (1 char diff)
            band="28MHz",
            mode="CW",
            frequency=28050,
            rst_sent="599", rst_received="599",
            exchange_sent="13", exchange_received="01",
            is_valid=True
        )

        contact2 = Contact(
            log_id=log_w1zzz.id,
            qso_datetime=datetime(2025, 3, 8, 18, 34, 30),
            call_received="LW5HR",
            band="28MHz",
            mode="CW",
            frequency=28050,
            rst_sent="599", rst_received="599",
            exchange_sent="01", exchange_received="13",
            is_valid=True
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        busted_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.BUSTED]
        assert len(busted_entries) == 1
        assert busted_entries[0].worked_callsign == "W1XZZ"
        assert busted_entries[0].suggested_call == "W1ZZZ"

    def test_not_busted_different_band(self, db_session, test_contest):
        """
        Case: Similar call exists but different band

        LW5HR logs LU6DX on 28MHz
        LU5DX has LW5HR on 14MHz (different band!)

        Expected: NOT BUSTED (different band = different QSO)
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_lu5dx = Log(contest_id=test_contest.id, callsign="LU5DX", operators="LU5DX")
        db_session.add_all([log_lw5hr, log_lu5dx])
        db_session.commit()

        contact1 = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 0),
            call_received="LU6DX",
            band="28MHz",  # 28MHz
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="13", exchange_received="14",
            is_valid=True
        )

        contact2 = Contact(
            log_id=log_lu5dx.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 15),
            call_received="LW5HR",
            band="14MHz",  # 14MHz - different band!
            mode="SSB",
            frequency=14200,
            rst_sent="59", rst_received="59",
            exchange_sent="14", exchange_received="13",
            is_valid=True
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Should NOT be busted (different band)
        busted_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.BUSTED]
        assert len(busted_entries) == 0

    def test_not_busted_different_mode(self, db_session, test_contest):
        """
        Case: Similar call exists but different mode

        LW5HR logs LU6DX on SSB
        LU5DX has LW5HR on CW (different mode!)

        Expected: NOT BUSTED (different mode = different QSO)
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_lu5dx = Log(contest_id=test_contest.id, callsign="LU5DX", operators="LU5DX")
        db_session.add_all([log_lw5hr, log_lu5dx])
        db_session.commit()

        contact1 = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 0),
            call_received="LU6DX",
            band="28MHz",
            mode="SSB",  # SSB
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="13", exchange_received="14",
            is_valid=True
        )

        contact2 = Contact(
            log_id=log_lu5dx.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 15),
            call_received="LW5HR",
            band="28MHz",
            mode="CW",  # CW - different mode!
            frequency=28050,
            rst_sent="599", rst_received="599",
            exchange_sent="14", exchange_received="13",
            is_valid=True
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Should NOT be busted (different mode)
        busted_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.BUSTED]
        assert len(busted_entries) == 0


class TestValidQSO:
    """Test valid QSO detection (no errors)"""

    def test_valid_qso_perfect_match(self, db_session, test_contest):
        """
        Case: Both stations logged correctly

        LW5HR logs LU5DX at 14:23
        LU5DX logs LW5HR at 14:23
        Same band, same mode, within tolerance

        Expected: No UBN entries for this QSO
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_lu5dx = Log(contest_id=test_contest.id, callsign="LU5DX", operators="LU5DX")
        db_session.add_all([log_lw5hr, log_lu5dx])
        db_session.commit()

        contact1 = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 0),
            call_received="LU5DX",
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="13", exchange_received="14",
            is_valid=True
        )

        contact2 = Contact(
            log_id=log_lu5dx.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 15),  # 15 seconds later
            call_received="LW5HR",
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="14", exchange_received="13",
            is_valid=True
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Should have no UBN entries (or entries for other contacts only)
        # These contacts should be valid
        stats = service.get_statistics(log_lw5hr.id)
        assert stats.matched_count >= 1  # At least this contact is matched


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_time_tolerance_boundary(self, db_session, test_contest):
        """
        Case: Test exactly at 1 minute boundary

        QSO at 14:23:00 vs 14:24:00 (exactly 60 seconds)

        Expected: Should match (within tolerance)
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_lu5dx = Log(contest_id=test_contest.id, callsign="LU5DX", operators="LU5DX")
        db_session.add_all([log_lw5hr, log_lu5dx])
        db_session.commit()

        contact1 = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 14, 23, 0),
            call_received="LU5DX",
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="13", exchange_received="14",
            is_valid=True
        )

        contact2 = Contact(
            log_id=log_lu5dx.id,
            qso_datetime=datetime(2025, 3, 8, 14, 24, 0),  # Exactly 60 seconds
            call_received="LW5HR",
            band="28MHz",
            mode="SSB",
            frequency=28500,
            rst_sent="59", rst_received="59",
            exchange_sent="14", exchange_received="13",
            is_valid=True
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Should match (within 1 minute tolerance)
        stats = service.get_statistics(log_lw5hr.id)
        assert stats.matched_count >= 1

    def test_multiple_similar_calls(self, db_session, test_contest):
        """
        Case: Multiple similar callsigns exist

        LW5HR logs W1ABC
        W1XBC submitted (has LW5HR)
        W1ABD submitted (no LW5HR)

        Expected: BUSTED to W1XBC (has reciprocal)
        """
        log_lw5hr = Log(contest_id=test_contest.id, callsign="LW5HR", operators="LW5HR")
        log_w1xbc = Log(contest_id=test_contest.id, callsign="W1XBC", operators="W1XBC")
        log_w1abd = Log(contest_id=test_contest.id, callsign="W1ABD", operators="W1ABD")
        db_session.add_all([log_lw5hr, log_w1xbc, log_w1abd])
        db_session.commit()

        contact1 = Contact(
            log_id=log_lw5hr.id,
            qso_datetime=datetime(2025, 3, 8, 16, 0, 0),
            call_received="W1ABC",  # Typo
            band="14MHz",
            mode="CW",
            frequency=14050,
            rst_sent="599", rst_received="599",
            exchange_sent="13", exchange_received="01",
            is_valid=True
        )

        # W1XBC has reciprocal
        contact2 = Contact(
            log_id=log_w1xbc.id,
            qso_datetime=datetime(2025, 3, 8, 16, 0, 20),
            call_received="LW5HR",
            band="14MHz",
            mode="CW",
            frequency=14050,
            rst_sent="599", rst_received="599",
            exchange_sent="01", exchange_received="13",
            is_valid=True
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        service = CrossCheckService(db_session)
        ubn_by_log = service.check_all_logs(test_contest.id)

        # Should suggest W1XBC (has reciprocal), not W1ABD
        busted_entries = [e for e in ubn_by_log[log_lw5hr.id] if e.ubn_type == UBNType.BUSTED]
        assert len(busted_entries) == 1
        assert busted_entries[0].suggested_call == "W1XBC"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

