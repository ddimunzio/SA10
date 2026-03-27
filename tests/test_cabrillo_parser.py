"""
Tests for Cabrillo parser

Tests parsing of Cabrillo format contest log files.
"""

import pytest
from pathlib import Path
import tempfile
from src.parsers.cabrillo import CabrilloParser, parse_cabrillo_file, CabrilloParseError


@pytest.fixture
def sample_cabrillo_log():
    """Sample minimal valid Cabrillo log"""
    return """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
CATEGORY-OPERATOR: SINGLE-OP
CATEGORY-BAND: 10M
CATEGORY-MODE: SSB
CATEGORY-POWER: HIGH
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC 59 4
QSO: 28450 PH 2025-03-08 1215 W1AW 59 5 K2DEF 59 3
END-OF-LOG:
"""


@pytest.fixture
def full_cabrillo_log():
    """Full Cabrillo log with all fields"""
    return """START-OF-LOG: 3.0
LOCATION: DX
CALLSIGN: 9M2J
CLUB: CARABAO DX TEAM
CONTEST: SA10-DX
CATEGORY-OPERATOR: MULTI-OP
CATEGORY-ASSISTED: ASSISTED
CATEGORY-BAND: ALL
CATEGORY-MODE: MIXED
CATEGORY-POWER: HIGH
CATEGORY-STATION: FIXED
CATEGORY-TRANSMITTER: ONE
CLAIMED-SCORE: 12096
OPERATORS: 9M2DOC 9W8ZZK/2 9M2WAZ
NAME: CARABAO DX TEAM
ADDRESS: 9370, JALAN KEKWA 2
ADDRESS: TAMAN GURU MELAYU
ADDRESS-CITY: SEREMBAN
ADDRESS-STATE-PROVINCE: NS
ADDRESS-POSTALCODE: 70450
ADDRESS-COUNTRY: WEST MALAYSIA
GRID-LOCATOR: OJ02XQ
EMAIL: carabaodxteam@gmail.com
CREATED-BY: N1MM Logger+ 1.0.10631.0
SOAPBOX: Great contest!
SOAPBOX: 10m was open all day
QSO: 28388 PH 2025-03-08 1228 9M2J 59 28 YB1CYO 59 28
QSO: 28388 PH 2025-03-08 1229 9M2J 59 28 YC1RGK 59 28
QSO: 28024 CW 2025-03-08 1554 9M2J 599 28 FY5KE 599 9
QSO: 28019 CW 2025-03-08 1721 9M2J 599 28 VU2TMP 599 22
END-OF-LOG:
"""


@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cbr') as f:
        yield f
        Path(f.name).unlink()


class TestCabrilloParser:
    """Test Cabrillo parser functionality"""

    def test_parse_minimal_log(self, sample_cabrillo_log, temp_file):
        """Test parsing a minimal valid log"""
        temp_file.write(sample_cabrillo_log)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.callsign == "W1AW"
        assert log.contest_name == "SA10M"
        assert log.category_operator == "SINGLE-OP"
        assert log.category_band == "10M"
        assert log.category_mode == "SSB"
        assert log.category_power == "HIGH"
        assert len(log.qsos) == 2
        assert len(log.parse_errors) == 0

    def test_parse_full_log(self, full_cabrillo_log, temp_file):
        """Test parsing a full log with all fields"""
        temp_file.write(full_cabrillo_log)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.callsign == "9M2J"
        assert log.contest_name == "SA10-DX"
        assert log.location == "DX"
        assert log.club == "CARABAO DX TEAM"
        assert log.claimed_score == 12096
        assert log.operators == "9M2DOC 9W8ZZK/2 9M2WAZ"
        assert log.name == "CARABAO DX TEAM"
        assert log.address_city == "SEREMBAN"
        assert log.address_state_province == "NS"
        assert log.address_country == "WEST MALAYSIA"
        assert log.grid_locator == "OJ02XQ"
        assert log.email == "carabaodxteam@gmail.com"
        assert log.created_by == "N1MM Logger+ 1.0.10631.0"
        assert len(log.soapbox) == 2
        assert "Great contest!" in log.soapbox
        assert len(log.qsos) == 4

    def test_parse_qso_lines(self, sample_cabrillo_log, temp_file):
        """Test QSO line parsing"""
        temp_file.write(sample_cabrillo_log)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        qso1 = log.qsos[0]
        assert qso1.frequency == 28400
        assert qso1.mode == "PH"
        assert qso1.qso_date == "2025-03-08"
        assert qso1.qso_time == "1200"
        assert qso1.call_sent == "W1AW"
        assert qso1.rst_sent == "59"
        assert qso1.exchange_sent == "5"
        assert qso1.call_received == "K1ABC"
        assert qso1.rst_received == "59"
        assert qso1.exchange_received == "4"

        qso2 = log.qsos[1]
        assert qso2.frequency == 28450
        assert qso2.call_received == "K2DEF"
        assert qso2.exchange_received == "3"

    def test_parse_mixed_modes(self, full_cabrillo_log, temp_file):
        """Test parsing CW and SSB QSOs"""
        temp_file.write(full_cabrillo_log)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        # Check SSB QSO
        ssb_qso = log.qsos[0]
        assert ssb_qso.mode == "PH"
        assert ssb_qso.rst_sent == "59"

        # Check CW QSO
        cw_qso = log.qsos[2]
        assert cw_qso.mode == "CW"
        assert cw_qso.rst_sent == "599"

    def test_missing_required_tags(self, temp_file):
        """Test detection of missing required tags"""
        incomplete_log = """START-OF-LOG: 3.0
CONTEST: SA10M
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC 59 4
END-OF-LOG:
"""
        temp_file.write(incomplete_log)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name, strict_mode=False)

        assert len(log.parse_errors) > 0
        assert any("CALLSIGN" in error for error in log.parse_errors)

    def test_strict_mode_errors(self, temp_file):
        """Test strict mode raises exception on errors"""
        incomplete_log = """START-OF-LOG: 3.0
CONTEST: SA10M
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC 59 4
END-OF-LOG:
"""
        temp_file.write(incomplete_log)
        temp_file.close()

        with pytest.raises(CabrilloParseError):
            parse_cabrillo_file(temp_file.name, strict_mode=True)

    def test_invalid_qso_format(self, temp_file):
        """Test handling of invalid QSO format"""
        bad_log = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
QSO: invalid line here
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC 59 4
END-OF-LOG:
"""
        temp_file.write(bad_log)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name, strict_mode=False)

        # Should parse the good QSO and log error for bad one
        assert len(log.qsos) == 1
        assert len(log.parse_errors) > 0

    def test_multi_line_address(self, full_cabrillo_log, temp_file):
        """Test multi-line ADDRESS field"""
        temp_file.write(full_cabrillo_log)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.address is not None
        assert "9370" in log.address
        assert "TAMAN GURU MELAYU" in log.address

    def test_file_not_found(self):
        """Test handling of missing file"""
        with pytest.raises(FileNotFoundError):
            parse_cabrillo_file("/nonexistent/file.cbr")

    def test_empty_file(self, temp_file):
        """Test handling of empty file"""
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name, strict_mode=False)

        assert len(log.parse_errors) > 0
        assert any("START-OF-LOG" in error for error in log.parse_errors)

    def test_no_qsos(self, temp_file):
        """Test log with no QSOs"""
        log_no_qsos = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
END-OF-LOG:
"""
        temp_file.write(log_no_qsos)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.callsign == "W1AW"
        assert len(log.qsos) == 0

    def test_callsign_normalization(self, temp_file):
        """Test callsign normalization to uppercase"""
        log_text = """START-OF-LOG: 3.0
CALLSIGN: w1aw
CONTEST: SA10M
QSO: 28400 PH 2025-03-08 1200 w1aw 59 5 k1abc 59 4
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.callsign.upper() == "W1AW"  # Can be normalized or not
        assert log.qsos[0].call_sent == "W1AW"  # QSO normalized
        assert log.qsos[0].call_received == "K1ABC"

    def test_mode_normalization(self, temp_file):
        """Test mode normalization"""
        log_text = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
QSO: 28400 SSB 2025-03-08 1200 W1AW 59 5 K1ABC 59 4
QSO: 28450 ph 2025-03-08 1215 W1AW 59 5 K2DEF 59 3
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        # Both should normalize to PH
        assert log.qsos[0].mode == "PH"
        assert log.qsos[1].mode == "PH"

    def test_transmitter_id(self, temp_file):
        """Test parsing transmitter ID"""
        log_text = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC 59 4 0
QSO: 28450 PH 2025-03-08 1215 W1AW 59 5 K2DEF 59 3 1
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.qsos[0].transmitter_id == "0"
        assert log.qsos[1].transmitter_id == "1"

    def test_real_log_file(self):
        """Test parsing actual SA10M log file"""
        log_path = Path("logs_sa10m_2025/9M2J_CW_SSB_JM153.txt")

        if not log_path.exists():
            pytest.skip("Test log file not available")

        log = parse_cabrillo_file(str(log_path))

        assert log.callsign == "9M2J"
        assert log.contest_name in ["SA10-DX", "SA10_DX"]
        assert len(log.qsos) > 0

        # Check first QSO
        qso = log.qsos[0]
        assert qso.frequency > 28000
        assert qso.frequency < 29000
        assert qso.mode in ["PH", "CW"]
        assert qso.call_sent == "9M2J"


class TestQSOParsing:
    """Test specific QSO parsing scenarios"""

    def test_parse_simple_exchange(self, temp_file):
        """Test parsing simple numeric exchange"""
        log_text = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC 59 4
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)
        qso = log.qsos[0]

        assert qso.exchange_sent == "5"
        assert qso.exchange_received == "4"

    def test_parse_multi_part_exchange(self, temp_file):
        """Test parsing multi-part exchange"""
        log_text = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
QSO: 28400 PH 2025-03-08 1200 W1AW 59 MA K1ABC 59 NH
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)
        qso = log.qsos[0]

        assert qso.exchange_sent == "MA"
        assert qso.exchange_received == "NH"

    def test_parse_portable_callsigns(self, temp_file):
        """Test parsing portable and mobile callsigns"""
        log_text = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC/M 59 4
QSO: 28450 PH 2025-03-08 1215 W1AW 59 5 K2DEF/P 59 3
QSO: 28500 PH 2025-03-08 1230 W1AW 59 5 W1AW/MM 59 5
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.qsos[0].call_received == "K1ABC/M"
        assert log.qsos[1].call_received == "K2DEF/P"
        assert log.qsos[2].call_received == "W1AW/MM"

    def test_frequency_validation(self, temp_file):
        """Test frequency validation"""
        log_text = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
QSO: 28400 PH 2025-03-08 1200 W1AW 59 5 K1ABC 59 4
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.qsos[0].frequency == 28400
        assert 28000 <= log.qsos[0].frequency <= 29000  # 10m band

    def test_float_frequency_format(self, temp_file):
        """
        CQ Logs Android and some other loggers write frequency as a float
        (e.g. "28000.00") instead of an integer.  The parser must handle this
        without producing a parse error and must return the correct integer kHz.

        Real-world trigger: LU3DSR_20260317_232829_2966.cbr logged 28000.00.
        """
        log_text = """START-OF-LOG: 3.0
CALLSIGN: LU3DSR
CONTEST: SA10M
QSO: 28000.00 PH 2025-03-15 1430 LU3DSR 59 13 LU7YE 59 13
QSO: 28450.50 CW 2025-03-15 1445 LU3DSR 599 13 PY1KJA 599 11
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        # No parse errors — the whole log must be accepted
        assert log.parse_errors == [], (
            f"Unexpected parse errors for float-frequency log: {log.parse_errors}"
        )
        assert len(log.qsos) == 2

        # Decimal part must be truncated, not rounded
        assert log.qsos[0].frequency == 28000
        assert log.qsos[1].frequency == 28450

    def test_float_frequency_edge_cases(self, temp_file):
        """
        Additional float-frequency edge cases:
        - ".0" suffix (no leading digit before decimal)
        - Large fractional part that still truncates to a valid integer
        """
        log_text = """START-OF-LOG: 3.0
CALLSIGN: W1AW
CONTEST: SA10M
QSO: 28000.9 PH 2025-03-15 1200 W1AW 59 5 K1ABC 59 4
QSO: 28999.0 PH 2025-03-15 1201 W1AW 59 5 K2DEF 59 3
END-OF-LOG:
"""
        temp_file.write(log_text)
        temp_file.close()

        log = parse_cabrillo_file(temp_file.name)

        assert log.parse_errors == [], (
            f"Unexpected parse errors: {log.parse_errors}"
        )
        assert len(log.qsos) == 2
        assert log.qsos[0].frequency == 28000   # truncated, not 28001
        assert log.qsos[1].frequency == 28999


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

