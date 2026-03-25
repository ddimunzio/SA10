"""
Tests for Log Import Service
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.services import LogImportService, import_cabrillo_to_db
from src.database.db_manager import DatabaseManager
from src.database.models import Contest, Log, Contact


@pytest.fixture
def db_manager():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db = DatabaseManager(db_path)
    db.create_all_tables()

    yield db

    # Cleanup
    db.engine.dispose()
    Path(db_path).unlink()

@pytest.fixture
def default_contest(db_manager):
    """Create a default contest for testing"""
    with db_manager.get_session() as session:
        contest = Contest(
            name="SA10M-TEST",
            slug="sa10m-test",
            start_date=datetime(2025, 3, 8, 0, 0, 0),
            end_date=datetime(2025, 3, 9, 23, 59, 59),
            rules_file="config/contests/SA10MC.txt"
        )
        session.add(contest)
        session.commit()
        session.refresh(contest)
        session.expunge(contest)
        return contest

@pytest.fixture
def import_service(db_manager):
    """Create log import service"""
    return LogImportService(db_manager)


@pytest.fixture
def sample_cabrillo_file():
    """Create a temporary Cabrillo file for testing"""
    content = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M-TEST
LOCATION: W1
CATEGORY-OPERATOR: SINGLE-OP
CATEGORY-BAND: 10M
CATEGORY-MODE: SSB
CATEGORY-POWER: HIGH
OPERATORS: W1AW
NAME: Hiram Percy Maxim
EMAIL: w1aw@arrl.org
CLAIMED-SCORE: 1000
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC 59 4
QSO: 28450 PH 2025-03-08 1215 W1AW 59 5 K2DEF 59 3
QSO: 28500 PH 2025-03-08 1230 W1AW 59 5 W3XYZ 59 4
END-OF-LOG:
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.cbr', delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


class TestLogImportService:
    """Test log import service functionality"""

    def test_import_single_log(self, import_service, sample_cabrillo_file, db_manager, default_contest):
        """Test importing a single log file"""
        result = import_service.import_cabrillo_file(sample_cabrillo_file, default_contest.id)

        assert result['success'] is True
        assert result['callsign'] == 'W1AW'
        assert result['qso_count'] == 3
        assert result['log_id'] is not None
        assert result['contest_id'] == default_contest.id

        # Verify in database
        with db_manager.get_session() as session:
            log = session.query(Log).filter(Log.id == result['log_id']).first()
            assert log is not None
            assert log.callsign == 'W1AW'
            assert log.category_operator == 'SINGLE-OP'
            assert log.claimed_score == 1000

            # Check QSOs
            qsos = session.query(Contact).filter(Contact.log_id == log.id).all()
            assert len(qsos) == 3
            assert qsos[0].call_sent == 'W1AW'
            assert qsos[0].call_received == 'K1ABC'

    def test_import_duplicate_log(self, import_service, sample_cabrillo_file, default_contest):
        """Test importing the same log twice"""
        # First import
        result1 = import_service.import_cabrillo_file(sample_cabrillo_file, default_contest.id)
        assert result1['success'] is True

        # Second import (should fail/skip)
        result2 = import_service.import_cabrillo_file(sample_cabrillo_file, default_contest.id)
        assert result2['success'] is False
        assert 'already exists' in result2['message'] or 'Skipped' in result2['message']

    def test_import_with_existing_contest(self, import_service, sample_cabrillo_file, db_manager):
        """Test importing to existing contest"""
        # Create contest first
        with db_manager.get_session() as session:
            contest = Contest(
                name='SA10M-EXISTING',
                slug='sa10m-existing',
                start_date=datetime(2025, 3, 8, 0, 0, 0),
                end_date=datetime(2025, 3, 9, 23, 59, 59),
                rules_file="config/contests/SA10MC.txt"
            )
            session.add(contest)
            session.commit()
            contest_id = contest.id

        # Import with specific contest_id
        result = import_service.import_cabrillo_file(
            sample_cabrillo_file,
            contest_id=contest_id
        )

        assert result['success'] is True
        assert result['contest_id'] == contest_id

    def test_import_file_not_found(self, import_service):
        """Test importing non-existent file"""
        result = import_service.import_cabrillo_file('/nonexistent/file.cbr', 1)

        assert result['success'] is False
        assert 'not found' in result['message'].lower()

    def test_qso_datetime_parsing(self, import_service, sample_cabrillo_file, db_manager, default_contest):
        """Test that QSO datetime is correctly parsed"""
        result = import_service.import_cabrillo_file(sample_cabrillo_file, default_contest.id)

        with db_manager.get_session() as session:
            qso = session.query(Contact).filter(
                Contact.log_id == result['log_id']
            ).first()

            assert qso.qso_datetime is not None
            assert qso.qso_datetime.year == 2025
            assert qso.qso_datetime.month == 3
            assert qso.qso_datetime.day == 8
            assert qso.qso_datetime.hour == 12
            assert qso.qso_datetime.minute == 0

    def test_band_detection(self, import_service, sample_cabrillo_file, db_manager, default_contest):
        """Test that band is correctly detected from frequency"""
        result = import_service.import_cabrillo_file(sample_cabrillo_file, default_contest.id)

        with db_manager.get_session() as session:
            qsos = session.query(Contact).filter(
                Contact.log_id == result['log_id']
            ).all()

            # All QSOs should be on 10m (28 MHz)
            for qso in qsos:
                assert qso.band == '10m'


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_import_cabrillo_to_db(self, sample_cabrillo_file):
        """Test convenience function"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = None
        try:
            # Pre-populate contest
            db = DatabaseManager(db_path)
            db.create_all_tables()
            with db.get_session() as session:
                contest = Contest(
                    name="SA10M-TEST",
                    slug="sa10m-test",
                    start_date=datetime(2025, 3, 8, 0, 0, 0),
                    end_date=datetime(2025, 3, 9, 23, 59, 59),
                    rules_file="config/contests/SA10MC.txt"
                )
                session.add(contest)
                session.commit()
                contest_id = contest.id
            
            # Now run import
            result = import_cabrillo_to_db(sample_cabrillo_file, contest_id, db_path)

            assert result['success'] is True
            assert result['callsign'] == 'W1AW'
            assert result['qso_count'] == 3

            # Verify database file was created
            assert Path(db_path).exists()

        finally:
            if db:
                db.engine.dispose()
            try:
                Path(db_path).unlink()
            except PermissionError:
                pass


class TestBatchImport:
    """Test directory batch import"""

    def test_import_directory(self, import_service, default_contest):
        """Test importing directory of logs"""
        # Skip if test logs directory doesn't exist
        if not Path('logs_sa10m_2025').exists():
            pytest.skip("Test logs directory not found")

        result = import_service.import_directory('logs_sa10m_2025', default_contest.id, pattern='CE1*.txt')

        assert result['total_files'] > 0
        # We can't guarantee success if files are bad, but we check structure
        assert 'details' in result

