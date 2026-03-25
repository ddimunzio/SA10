"""
Ham Radio Utilities using pyhamtools

This module provides utilities for:
- Callsign parsing and validation
- DXCC entity lookup
- CQ zone lookup
- Prefix extraction
- Country/continent determination
"""

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import re
import logging

try:
    from pyhamtools import LookupLib, Callinfo
    from pyhamtools.locator import calculate_distance, calculate_heading
    PYHAMTOOLS_AVAILABLE = True
except ImportError:
    PYHAMTOOLS_AVAILABLE = False
    logging.warning("pyhamtools not installed. Some features will be limited.")

logger = logging.getLogger(__name__)


@dataclass
class CallsignInfo:
    """Information about a callsign"""
    callsign: str
    prefix: str
    country: str
    continent: str
    cq_zone: int
    itu_zone: int
    dxcc_entity: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_valid: bool = True
    error: Optional[str] = None


class HamRadioUtils:
    """
    Utilities for ham radio operations using pyhamtools
    """

    def __init__(self):
        """Initialize the lookup library"""
        self.lookup_lib = None
        if PYHAMTOOLS_AVAILABLE:
            try:
                self.lookup_lib = LookupLib(lookuptype="countryfile")
                logger.info("pyhamtools LookupLib initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize pyhamtools: {e}")
                self.lookup_lib = None

    def get_callsign_info(self, callsign: str) -> CallsignInfo:
        """
        Get comprehensive information about a callsign

        Args:
            callsign: Amateur radio callsign

        Returns:
            CallsignInfo object with all available data
        """
        # Clean the callsign
        callsign = self._clean_callsign(callsign)

        if not self.lookup_lib:
            # Fallback to basic parsing if pyhamtools not available
            return self._basic_callsign_parse(callsign)

        try:
            # Use pyhamtools to get callsign info
            cic = Callinfo(self.lookup_lib)
            info = cic.get_all(callsign)

            return CallsignInfo(
                callsign=callsign,
                prefix=self.extract_wpx_prefix(callsign),
                country=info.get('country', 'Unknown'),
                continent=info.get('continent', 'Unknown'),
                cq_zone=int(info.get('cq', 0)),
                itu_zone=int(info.get('itu', 0)),
                dxcc_entity=int(info.get('adif', 0)),
                latitude=info.get('latitude'),
                longitude=info.get('longitude'),
                is_valid=True,
                error=None
            )
        except Exception as e:
            logger.warning(f"Error looking up callsign {callsign}: {e}")
            return CallsignInfo(
                callsign=callsign,
                prefix=self.extract_wpx_prefix(callsign),
                country='Unknown',
                continent='Unknown',
                cq_zone=0,
                itu_zone=0,
                dxcc_entity=0,
                is_valid=False,
                error=str(e)
            )

    def _clean_callsign(self, callsign: str) -> str:
        """
        Clean a callsign by removing common suffixes and prefixes

        Args:
            callsign: Raw callsign

        Returns:
            Cleaned callsign
        """
        callsign = callsign.upper().strip()

        # Remove common portable indicators for lookup
        # But keep them for WPX prefix extraction
        lookup_call = callsign

        # Remove /P, /M, /QRP, /B, /A etc at the end
        lookup_call = re.sub(r'/[PMQRPBA]+$', '', lookup_call)

        # Remove /MM (maritime mobile) or /AM (aeronautical mobile)
        lookup_call = re.sub(r'/(MM|AM)$', '', lookup_call)

        return lookup_call

    def extract_wpx_prefix(self, callsign: str) -> str:
        """
        Extract WPX (Worked All Prefixes) prefix from a callsign

        The WPX prefix consists of:
        - All characters before the first digit
        - Plus the first digit

        Examples:
            W1AW -> W1
            LU1HLH -> LU1
            DL2025B -> DL2
            VE3/W1AW -> VE3
            W1AW/4 -> W1

        Args:
            callsign: Amateur radio callsign

        Returns:
            WPX prefix
        """
        callsign = callsign.upper().strip()

        # Handle portable operations (prefix/call or call/suffix)
        if '/' in callsign:
            parts = callsign.split('/')

            # If first part has a digit, it's the prefix (e.g., VE3/W1AW)
            if any(c.isdigit() for c in parts[0]):
                callsign = parts[0]
            else:
                # Otherwise use the main call (e.g., W1AW/4)
                callsign = parts[0] if len(parts[0]) > len(parts[1]) else parts[1]

        # Find first digit
        match = re.search(r'\d', callsign)
        if match:
            digit_pos = match.start()
            # Prefix is everything up to and including the first digit
            return callsign[:digit_pos + 1]

        # No digit found - shouldn't happen for valid callsigns
        return callsign

    def _basic_callsign_parse(self, callsign: str) -> CallsignInfo:
        """
        Basic callsign parsing when pyhamtools is not available

        Args:
            callsign: Callsign to parse

        Returns:
            CallsignInfo with basic data
        """
        prefix = self.extract_wpx_prefix(callsign)

        # Basic prefix to country mapping
        country_map = {
            'LU': 'Argentina', 'W': 'United States', 'K': 'United States',
            'N': 'United States', 'VE': 'Canada', 'CE': 'Chile',
            'PY': 'Brazil', 'CX': 'Uruguay', 'YV': 'Venezuela',
            'EA': 'Spain', 'F': 'France', 'G': 'England',
            'DL': 'Germany', 'I': 'Italy', 'JA': 'Japan'
        }

        # Extract base prefix (without number)
        base_prefix = prefix.rstrip('0123456789')
        country = country_map.get(base_prefix, 'Unknown')

        return CallsignInfo(
            callsign=callsign,
            prefix=prefix,
            country=country,
            continent='Unknown',
            cq_zone=0,
            itu_zone=0,
            dxcc_entity=0,
            is_valid=True,
            error="pyhamtools not available - using basic parsing"
        )

    def validate_callsign_format(self, callsign: str) -> bool:
        """
        Validate that a callsign has a proper format

        Basic rules:
        - Must have at least one letter
        - Must have at least one digit
        - Can contain letters, digits, and /

        Args:
            callsign: Callsign to validate

        Returns:
            True if format is valid
        """
        callsign = callsign.upper().strip()

        if not callsign:
            return False

        # Must have at least one letter and one digit
        has_letter = any(c.isalpha() for c in callsign)
        has_digit = any(c.isdigit() for c in callsign)

        if not (has_letter and has_digit):
            return False

        # Only allow letters, digits, and /
        if not re.match(r'^[A-Z0-9/]+$', callsign):
            return False

        return True

    def calculate_distance_and_bearing(
        self,
        from_grid: str,
        to_grid: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate distance and bearing between two Maidenhead grid locators

        Args:
            from_grid: Source grid locator (e.g., "FN31pr")
            to_grid: Destination grid locator

        Returns:
            Tuple of (distance_km, bearing_degrees) or (None, None) if error
        """
        if not PYHAMTOOLS_AVAILABLE:
            logger.warning("pyhamtools not available for distance calculation")
            return None, None

        try:
            distance = calculate_distance(from_grid, to_grid)
            bearing = calculate_heading(from_grid, to_grid)
            return distance, bearing
        except Exception as e:
            logger.error(f"Error calculating distance/bearing: {e}")
            return None, None

    def get_dxcc_info(self, callsign: str) -> Dict[str, Any]:
        """
        Get DXCC entity information for a callsign

        Args:
            callsign: Amateur radio callsign

        Returns:
            Dictionary with DXCC information
        """
        info = self.get_callsign_info(callsign)

        return {
            'callsign': info.callsign,
            'dxcc_entity': info.dxcc_entity,
            'country': info.country,
            'continent': info.continent,
            'prefix': info.prefix
        }

    def get_zone_info(self, callsign: str) -> Dict[str, int]:
        """
        Get CQ and ITU zone information for a callsign

        Args:
            callsign: Amateur radio callsign

        Returns:
            Dictionary with zone information
        """
        info = self.get_callsign_info(callsign)

        return {
            'callsign': info.callsign,
            'cq_zone': info.cq_zone,
            'itu_zone': info.itu_zone
        }


# Global instance
_ham_utils_instance = None

def get_ham_utils() -> HamRadioUtils:
    """
    Get singleton instance of HamRadioUtils

    Returns:
        HamRadioUtils instance
    """
    global _ham_utils_instance
    if _ham_utils_instance is None:
        _ham_utils_instance = HamRadioUtils()
    return _ham_utils_instance


# Convenience functions
def extract_wpx_prefix(callsign: str) -> str:
    """Extract WPX prefix from callsign"""
    return get_ham_utils().extract_wpx_prefix(callsign)

def get_callsign_info(callsign: str) -> CallsignInfo:
    """Get information about a callsign"""
    return get_ham_utils().get_callsign_info(callsign)

def validate_callsign(callsign: str) -> bool:
    """Validate callsign format"""
    return get_ham_utils().validate_callsign_format(callsign)

def get_cq_zone(callsign: str) -> int:
    """Get CQ zone for a callsign"""
    info = get_callsign_info(callsign)
    return info.cq_zone


if __name__ == "__main__":
    # Demo usage
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        callsign = sys.argv[1]
    else:
        callsign = "LU1HLH"

    print(f"\nLooking up: {callsign}\n")

    utils = HamRadioUtils()

    # Get full info
    info = utils.get_callsign_info(callsign)
    print(f"Callsign: {info.callsign}")
    print(f"WPX Prefix: {info.prefix}")
    print(f"Country: {info.country}")
    print(f"Continent: {info.continent}")
    print(f"CQ Zone: {info.cq_zone}")
    print(f"ITU Zone: {info.itu_zone}")
    print(f"DXCC Entity: {info.dxcc_entity}")
    if info.latitude and info.longitude:
        print(f"Location: {info.latitude}, {info.longitude}")

    # Test WPX prefix extraction
    test_calls = ["W1AW", "LU1HLH", "VE3/W1AW", "W1AW/4", "DL2025B"]
    print(f"\nWPX Prefix extraction:")
    for call in test_calls:
        prefix = utils.extract_wpx_prefix(call)
        print(f"  {call:15} -> {prefix}")

