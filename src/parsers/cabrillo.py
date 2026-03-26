"""
Cabrillo Log File Parser

Parses Cabrillo format contest log files according to WWROF Cabrillo v3.0 specification.
See: https://wwrof.org/cabrillo/

Supports:
- All standard Cabrillo header tags
- QSO line parsing with flexible column handling
- Format validation
- Error reporting with line numbers
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
import logging

from ..core.models.contact import ContactBase
from ..core.models.log import LogBase

logger = logging.getLogger(__name__)


class CabrilloQSO(ContactBase):
    """Extended contact model with Cabrillo-specific fields"""
    line_number: Optional[int] = Field(None, description="Line number in source file")
    raw_line: Optional[str] = Field(None, description="Original QSO line from file")
    validation_reason: Optional[str] = Field(None, description="Reason for validation failure during import")


class CabrilloLog(LogBase):
    """Extended log model with Cabrillo-specific fields"""
    qsos: List[CabrilloQSO] = Field(default_factory=list, description="List of QSOs")
    claimed_score: Optional[int] = Field(None, description="Claimed score from log")
    created_by: Optional[str] = Field(None, description="Software that created the log")
    offtime: Optional[str] = Field(None, description="Off-time declaration")
    soapbox: List[str] = Field(default_factory=list, description="Soapbox comments")

    # Additional fields from Cabrillo
    arrl_section: Optional[str] = Field(None, description="ARRL section")
    certificate: Optional[str] = Field(None, description="Certificate requested")
    debug: Optional[str] = Field(None, description="Debug info")
    iota: Optional[str] = Field(None, description="IOTA reference")

    # Metadata
    file_path: Optional[str] = Field(None, description="Source file path")
    parse_errors: List[str] = Field(default_factory=list, description="Parse errors")
    parse_warnings: List[str] = Field(default_factory=list, description="Parse warnings")


class CabrilloParseError(Exception):
    """Exception raised for Cabrillo parsing errors"""
    pass


class CabrilloParser:
    """
    Parser for Cabrillo format contest log files.

    Follows WWROF Cabrillo v3.0 specification.
    """

    # Cabrillo header tag patterns
    TAG_PATTERN = re.compile(r'^([A-Z][A-Z0-9-]*):(.*)$')
    QSO_PATTERN = re.compile(r'^QSO:\s+(.+)$')

    # Required header tags
    REQUIRED_TAGS = ['START-OF-LOG', 'CALLSIGN', 'CONTEST']

    # Valid category tags
    CATEGORY_TAGS = {
        'CATEGORY-ASSISTED', 'CATEGORY-BAND', 'CATEGORY-MODE',
        'CATEGORY-OPERATOR', 'CATEGORY-OVERLAY', 'CATEGORY-POWER',
        'CATEGORY-STATION', 'CATEGORY-TIME', 'CATEGORY-TRANSMITTER'
    }

    # Tags that can appear multiple times
    MULTI_VALUE_TAGS = {'SOAPBOX', 'ADDRESS', 'OFFTIME'}

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the Cabrillo parser.

        Args:
            strict_mode: If True, raise exceptions on validation errors.
                        If False, collect errors and warnings.
        """
        self.strict_mode = strict_mode
        self.reset()

    def reset(self):
        """Reset parser state"""
        self.header_data: Dict[str, Any] = {}
        self.qsos: List[CabrilloQSO] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.line_number = 0

    def parse_file(self, file_path: str) -> CabrilloLog:
        """
        Parse a Cabrillo log file.

        Args:
            file_path: Path to the Cabrillo file

        Returns:
            CabrilloLog object with parsed data

        Raises:
            CabrilloParseError: If file cannot be parsed (in strict mode)
            FileNotFoundError: If file does not exist
        """
        self.reset()
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Parsing Cabrillo file: {file_path}")

        # Read file with multiple encoding attempts
        content = self._read_file(path)

        # Parse line by line
        in_log = False
        found_start_tag = False
        for line_num, line in enumerate(content.split('\n'), 1):
            self.line_number = line_num
            line = line.rstrip('\r\n')

            # Skip empty lines
            if not line.strip():
                continue

            # Check for START-OF-LOG (handle common typo: SSBSTART-OF-LOG)
            if line.startswith('START-OF-LOG:') or 'START-OF-LOG:' in line:
                in_log = True
                found_start_tag = True
                # Fix common typo: SSBSTART-OF-LOG -> START-OF-LOG
                if not line.startswith('START-OF-LOG:'):
                    line = line[line.index('START-OF-LOG:'):]
                    self._add_warning(f"Line {line_num}: Fixed malformed START-OF-LOG tag")
                self._parse_tag_line(line)
                continue

            # Check for END-OF-LOG
            if line.startswith('END-OF-LOG:'):
                in_log = False
                break

            # If we haven't found START-OF-LOG yet but see a valid tag or QSO, assume we're in the log
            if not found_start_tag and (line.startswith('QSO:') or ':' in line):
                if not in_log:
                    self._add_warning(f"Line {line_num}: File missing START-OF-LOG tag, parsing anyway")
                    in_log = True
                    found_start_tag = True  # Prevent repeated warnings

            if not in_log:
                self._add_warning(f"Line {line_num}: Content before START-OF-LOG ignored")
                continue

            # Parse QSO line
            if line.startswith('QSO:'):
                self._parse_qso_line(line, line_num)
            # Parse header tag
            else:
                self._parse_tag_line(line)

        # Validate required tags
        self._validate_required_tags()

        # Build and return CabrilloLog object
        return self._build_log_object(file_path)

    def _read_file(self, path: Path) -> str:
        """Read file with encoding detection"""
        encodings = ['utf-8', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue

        # Fallback: read as bytes and decode with errors='replace'
        self._add_warning(f"Could not decode file with standard encodings, using fallback")
        return path.read_bytes().decode('utf-8', errors='replace')

    def _parse_tag_line(self, line: str):
        """Parse a header tag line"""
        match = self.TAG_PATTERN.match(line)
        if not match:
            self._add_warning(f"Line {self.line_number}: Invalid tag format: {line[:50]}")
            return

        tag = match.group(1).strip()
        value = match.group(2).strip()

        # Handle multi-value tags
        if tag in self.MULTI_VALUE_TAGS:
            if tag not in self.header_data:
                self.header_data[tag] = []
            self.header_data[tag].append(value)
        else:
            # Warn if tag is redefined
            if tag in self.header_data:
                self._add_warning(f"Line {self.line_number}: Tag {tag} redefined")
            self.header_data[tag] = value

    def _parse_frequency(self, freq_str: str) -> int:
        """
        Parse frequency string which might be a frequency in kHz or a band name.
        
        Handles:
        - Standard frequency in kHz (e.g. "28000")
        - Band names with 'm' (e.g. "10m", "15m")
        - Band names without 'm' (e.g. "10", "15")
        """
        # Try to parse as integer first
        if freq_str.isdigit():
            val = int(freq_str)
            # If it looks like a valid frequency (>= 1800 kHz), return it
            # Note: 160m band starts at 1800 kHz.
            # If input is "160", it is < 1800, so we treat as band.
            if val >= 1800:
                return val
            
        # Handle band names
        s = freq_str.lower()
        
        # Map band names to representative frequencies (start of band)
        band_map = {
            '160m': 1800, '160': 1800,
            '80m': 3500, '80': 3500,
            '40m': 7000, '40': 7000,
            '30m': 10100, '30': 10100,
            '20m': 14000, '20': 14000,
            '17m': 18068, '17': 18068,
            '15m': 21000, '15': 21000,
            '12m': 24890, '12': 24890,
            '10m': 28000, '10': 28000,
            '6m': 50000, '6': 50000,
            '2m': 144000, '2': 144000,
            '70cm': 432000, '70': 432000
        }
        
        if s in band_map:
            return band_map[s]

        # Handle float-format frequencies like "28000.00"
        try:
            return int(float(freq_str))
        except (ValueError, TypeError):
            pass

        # Fallback to int conversion which will raise ValueError if invalid
        return int(freq_str)

    def _parse_qso_line(self, line: str, line_num: int):
        """
        Parse a QSO line.

        Cabrillo QSO format:
        QSO: freq  mo date       time call          rst exch   call          rst exch   t
        QSO: 28388 PH 2025-03-08 1228 9M2J          59  28     YB1CYO        59  28
        """
        try:
            # Remove "QSO:" prefix
            qso_data = line[4:].strip()

            # Split by whitespace (filter empty strings from multiple spaces)
            parts = [p for p in qso_data.split() if p]

            # Minimum: freq mode date time tx_call tx_rst tx_exch rx_call
            # We'll be lenient with missing rx_rst and rx_exch (mark as warnings)
            if len(parts) < 8:
                self._add_error(f"Line {line_num}: Invalid QSO format (too few fields, minimum 8 required): {line[:80]}")
                return

            # Parse fields (Cabrillo v3.0 format)
            # Format: freq mode date time tx_call tx_rst tx_exch rx_call rx_rst rx_exch [transmitter_id]
            try:
                frequency = self._parse_frequency(parts[0])
                mode = parts[1].upper()
                qso_date = parts[2]
                qso_time = parts[3]
                call_sent = parts[4].upper()

                # Find where received callsign starts (it's the first field that looks like a callsign after exchange_sent)
                # RST and exchange can be multi-part, so we need to find the received callsign
                # Heuristic: callsign contains letters and numbers, exchange is often just numbers

                # For SA10M: RST (2-3 digits) + CQ_ZONE (1-2 digits)
                # So sent exchange is parts[5] and parts[6] (if zone is 2 digits) or just parts[5] if combined

                # Better approach: work backwards from the end
                # Last field might be transmitter_id (0 or T)
                # Before that: rx_exch (1-2 fields)
                # Before that: rx_rst (1 field)
                # Before that: rx_call (1 field)
                # Before that: tx_exch (1-2 fields)
                # Before that: tx_rst (1 field)

                # Simple approach for SA10M: assume fixed format
                # tx_rst tx_exch rx_call rx_rst rx_exch [tx_id]

                # Detect transmitter ID (last field might be 0, 1, 2, or single letter)
                transmitter_id = None
                if len(parts) > 10 and len(parts[-1]) <= 2:
                    # Might be transmitter ID
                    if parts[-1].isdigit() or parts[-1].isalpha():
                        transmitter_id = parts[-1]
                        parts = parts[:-1]  # Remove it from parts

                # Now parse: parts[5..8] are rst_sent, exch_sent, call_received, rst_received
                # and remaining are exchange_received
                # Allow 8+ fields (lenient mode - missing exchanges will be imported but marked with warnings)
                if len(parts) >= 8:
                    rst_sent = parts[5]

                    # Exchange sent: could be 1 or more fields
                    # Find received callsign (contains letters and at least one digit)
                    rx_call_idx = None
                    for i in range(6, len(parts)):
                        if self._looks_like_callsign(parts[i]):
                            rx_call_idx = i
                            break

                    if rx_call_idx is None:
                        # No callsign found by strict rules - try less strict
                        # Look for a field that has at least 3 characters
                        for i in range(6, len(parts)):
                            if len(parts[i]) >= 3 and parts[i].isalnum():
                                rx_call_idx = i
                                self._add_warning(f"Line {line_num}: Received callsign may be invalid (no number detected): {parts[i]}")
                                break

                    if rx_call_idx is None:
                        self._add_error(f"Line {line_num}: Cannot find received callsign: {line[:80]}")
                        return

                    # Exchange sent is everything between rst_sent and rx_call
                    exchange_sent = ' '.join(parts[6:rx_call_idx])
                    call_received = parts[rx_call_idx].upper()

                    # After rx_call: rst_received and exchange_received
                    # Be lenient with missing fields - import them with empty values
                    # Track validation issues to be saved in database
                    validation_issues = []

                    # Check if received callsign looks valid (should have at least one number)
                    if not any(c.isdigit() for c in call_received):
                        validation_issues.append(f"Invalid callsign format: {call_received}")

                    if len(parts) > rx_call_idx + 1:
                        rst_received = parts[rx_call_idx + 1]
                        # Check if there's an exchange after RST
                        if len(parts) > rx_call_idx + 2:
                            exchange_received = ' '.join(parts[rx_call_idx + 2:])
                        else:
                            # Missing exchange - mark as warning but import anyway
                            exchange_received = ''
                            validation_issues.append("Missing received exchange")
                            self._add_warning(f"Line {line_num}: Missing received exchange (will be marked invalid during validation)")
                    else:
                        # Missing both RST and exchange
                        rst_received = ''
                        exchange_received = ''
                        validation_issues.append("Missing received RST and exchange")
                        self._add_warning(f"Line {line_num}: Missing received RST and exchange (will be marked invalid during validation)")

                    # Validate date format
                    if not self._validate_date(qso_date):
                        self._add_warning(f"Line {line_num}: Invalid date format: {qso_date}")

                    # Validate and normalize time format (convert HH:MM to HHMM)
                    qso_time = self._normalize_time(qso_time)
                    if not self._validate_time(qso_time):
                        self._add_warning(f"Line {line_num}: Invalid time format: {qso_time}")

                    # Create QSO object with validation reason if any issues found
                    validation_reason = "; ".join(validation_issues) if validation_issues else None

                    qso = CabrilloQSO(
                        frequency=frequency,
                        mode=mode,
                        qso_date=qso_date,
                        qso_time=qso_time,
                        call_sent=call_sent,
                        rst_sent=rst_sent,
                        exchange_sent=exchange_sent,
                        call_received=call_received,
                        rst_received=rst_received,
                        exchange_received=exchange_received,
                        transmitter_id=transmitter_id,
                        line_number=line_num,
                        raw_line=line,
                        validation_reason=validation_reason
                    )

                    self.qsos.append(qso)

                else:
                    self._add_error(f"Line {line_num}: Invalid QSO format: {line[:80]}")

            except (ValueError, IndexError) as e:
                self._add_error(f"Line {line_num}: Error parsing QSO: {e}")

        except Exception as e:
            self._add_error(f"Line {line_num}: Unexpected error parsing QSO: {e}")

    def _looks_like_callsign(self, s: str) -> bool:
        """Check if a string looks like a callsign"""
        s = s.upper()
        has_letter = any(c.isalpha() for c in s)
        has_number = any(c.isdigit() for c in s)
        return has_letter and has_number and len(s) >= 3

    def _validate_date(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _normalize_time(self, time_str: str) -> str:
        """Normalize time format - convert HH:MM to HHMM"""
        if ':' in time_str:
            # Convert HH:MM to HHMM
            parts = time_str.split(':')
            if len(parts) == 2:
                return parts[0].zfill(2) + parts[1].zfill(2)
        return time_str

    def _validate_time(self, time_str: str) -> bool:
        """Validate time format (HHMM)"""
        if len(time_str) != 4 or not time_str.isdigit():
            return False
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        return 0 <= hour <= 23 and 0 <= minute <= 59

    def _validate_required_tags(self):
        """Validate that all required tags are present"""
        for tag in self.REQUIRED_TAGS:
            if tag not in self.header_data:
                self._add_error(f"Missing required tag: {tag}")

    def _build_log_object(self, file_path: str) -> CabrilloLog:
        """Build CabrilloLog object from parsed data"""
        try:
            # Map header data to log fields
            log_data = {
                'file_path': file_path,
                'qsos': self.qsos,
                'parse_errors': self.errors,
                'parse_warnings': self.warnings,
            }

            # Map Cabrillo tags to model fields
            tag_mapping = {
                'CALLSIGN': 'callsign',
                'CONTEST': 'contest_name',
                'START-OF-LOG': 'cabrillo_version',
                'LOCATION': 'location',
                'CLUB': 'club',
                'CATEGORY-OPERATOR': 'category_operator',
                'CATEGORY-ASSISTED': 'category_assisted',
                'CATEGORY-BAND': 'category_band',
                'CATEGORY-MODE': 'category_mode',
                'CATEGORY-POWER': 'category_power',
                'CATEGORY-STATION': 'category_station',
                'CATEGORY-TRANSMITTER': 'category_transmitter',
                'CATEGORY-OVERLAY': 'category_overlay',
                'CATEGORY-TIME': 'category_time',
                'OPERATORS': 'operators',
                'NAME': 'name',
                'ADDRESS-CITY': 'address_city',
                'ADDRESS-STATE-PROVINCE': 'address_state_province',
                'ADDRESS-POSTALCODE': 'address_postalcode',
                'ADDRESS-COUNTRY': 'address_country',
                'GRID-LOCATOR': 'grid_locator',
                'EMAIL': 'email',
                'CLAIMED-SCORE': 'claimed_score',
                'CREATED-BY': 'created_by',
                'ARRL-SECTION': 'arrl_section',
                'CERTIFICATE': 'certificate',
                'IOTA': 'iota',
            }

            # Map tags to fields
            for tag, field in tag_mapping.items():
                if tag in self.header_data:
                    value = self.header_data[tag]
                    # Convert numeric fields
                    if field == 'claimed_score':
                        if value and value.strip():
                            try:
                                value = int(value.strip())
                            except ValueError:
                                self._add_warning(f"Invalid CLAIMED-SCORE value: {value}")
                                value = None
                        else:
                            value = None
                    # Convert empty email to None to avoid validation errors
                    # Also handle invalid email formats by setting to None
                    if field == 'email':
                        if not value or not value.strip():
                            value = None
                        else:
                            # Basic cleanup - remove trailing dots and double dots
                            value = value.strip().rstrip('.')
                            value = value.replace('..', '.')
                            # If still invalid, set to None to allow import
                            if not value or '@' not in value:
                                value = None
                    log_data[field] = value

            # Handle multi-line ADDRESS
            if 'ADDRESS' in self.header_data:
                log_data['address'] = '\n'.join(self.header_data['ADDRESS'])

            # Handle SOAPBOX
            if 'SOAPBOX' in self.header_data:
                log_data['soapbox'] = self.header_data['SOAPBOX']

            # Handle OFFTIME
            if 'OFFTIME' in self.header_data:
                log_data['offtime'] = '\n'.join(self.header_data['OFFTIME'])

            # Ensure required fields have defaults if missing
            if 'callsign' not in log_data:
                # Try to extract from filename (format: CALLSIGN_MODE_ID.txt)
                filename = Path(file_path).stem
                parts = filename.split('_')
                log_data['callsign'] = parts[0] if parts else 'UNKNOWN'
            
            if 'contest_name' not in log_data:
                log_data['contest_name'] = 'SA10M'  # Default to SA10M

            # Create log object
            log = CabrilloLog(**log_data)

            # Check for errors in strict mode
            if self.strict_mode and self.errors:
                raise CabrilloParseError(f"Parse errors: {'; '.join(self.errors)}")

            logger.info(f"Successfully parsed {len(self.qsos)} QSOs from {file_path}")
            if self.warnings:
                logger.warning(f"Parse warnings: {len(self.warnings)}")
            if self.errors:
                logger.error(f"Parse errors: {len(self.errors)}")

            return log

        except ValidationError as e:
            error_msg = f"Validation error creating log object: {e}"
            self._add_error(error_msg)
            if self.strict_mode:
                raise CabrilloParseError(error_msg)
            # Return log with errors - use defaults for missing required fields
            # Extract callsign from filename if not in header
            callsign = self.header_data.get('CALLSIGN', 'UNKNOWN')
            if callsign == 'UNKNOWN':
                # Try to extract from filename (format: CALLSIGN_MODE_ID.txt)
                filename = Path(file_path).stem
                parts = filename.split('_')
                if parts:
                    callsign = parts[0]
            
            return CabrilloLog(
                callsign=callsign,
                contest_name=self.header_data.get('CONTEST', 'SA10M'),  # Default to SA10M
                file_path=file_path,
                qsos=self.qsos,
                parse_errors=self.errors,
                parse_warnings=self.warnings
            )

    def _add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)
        logger.error(message)

    def _add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)
        logger.warning(message)


def parse_cabrillo_file(file_path: str, strict_mode: bool = False) -> CabrilloLog:
    """
    Convenience function to parse a Cabrillo file.

    Args:
        file_path: Path to the Cabrillo file
        strict_mode: If True, raise exceptions on validation errors

    Returns:
        CabrilloLog object with parsed data
    """
    parser = CabrilloParser(strict_mode=strict_mode)
    return parser.parse_file(file_path)

