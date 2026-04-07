from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Contest, Log, Contact as DBContact
from src.services.ubn_report_generator import UBNReportGenerator
from src.utils import cq_zones_match, extract_cq_zone, normalize_cq_zone


def Contact(**kwargs):
    if 'qso_datetime' in kwargs:
        dt = kwargs['qso_datetime']
        kwargs.setdefault('qso_date', dt.strftime('%Y-%m-%d'))
        kwargs.setdefault('qso_time', dt.strftime('%H%M'))

    kwargs.setdefault('call_sent', 'TEST_STATION')
    return DBContact(**kwargs)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def test_contest(db_session):
    contest = Contest(
        name="Test Contest 2025",
        slug="test-exchange-normalization",
        start_date=datetime(2025, 3, 8, 0, 0, 0),
        end_date=datetime(2025, 3, 9, 23, 59, 59),
        rules_file="config/contests/SA10MC.txt",
    )
    db_session.add(contest)
    db_session.commit()
    return contest


def test_extract_cq_zone_from_noisy_exchange():
    assert extract_cq_zone("13 AY7") == "13"
    assert extract_cq_zone("04") == "4"
    assert normalize_cq_zone("13 AY7") == "13"
    assert cq_zones_match("13 AY7", "13") is True


def test_reverse_exchange_report_ignores_trailing_tokens(db_session, test_contest):
    my_log = Log(contest_id=test_contest.id, callsign="AY7J", operators="AY7J")
    other_log = Log(contest_id=test_contest.id, callsign="N6AR", operators="N6AR")
    db_session.add_all([my_log, other_log])
    db_session.commit()

    my_contact = Contact(
        log_id=my_log.id,
        qso_datetime=datetime(2026, 3, 14, 20, 13, 0),
        call_received="N6AR",
        band="10m",
        mode="CW",
        frequency=28040,
        rst_sent="599",
        rst_received="599",
        exchange_sent="13",
        exchange_received="3",
        is_valid=True,
    )
    other_contact = Contact(
        log_id=other_log.id,
        qso_datetime=datetime(2026, 3, 14, 20, 13, 0),
        call_received="AY7J",
        band="10m",
        mode="CW",
        frequency=28040,
        rst_sent="599",
        rst_received="599",
        exchange_sent="3",
        exchange_received="13 AY7",
        is_valid=True,
    )
    db_session.add_all([my_contact, other_contact])
    db_session.commit()

    generator = UBNReportGenerator(db_session)

    assert generator._get_reverse_exchange_errors(my_log.id) == []