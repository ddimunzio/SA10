"""
Callsign Lookup Service

Provides callsign prefix lookups using CTY data from the database.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..database.models import CTYData
import re


class CallsignLookupService:
    """Service for looking up callsign information from CTY data."""
    
    def __init__(self, session: Session):
        """
        Initialize the lookup service.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cty_data: Optional[List] = None  # Cache all CTY data on first use
        
    def lookup_callsign(self, callsign: str) -> Optional[Dict[str, Any]]:
        """
        Look up DXCC information for a callsign.
        
        Args:
            callsign: The callsign to look up
            
        Returns:
            Dictionary with continent, country_name, dxcc_code, cq_zone, etc.
            None if not found
        """
        if not callsign:
            return None
            
        # Check cache
        if callsign in self._cache:
            return self._cache[callsign]
        
        # Clean callsign (remove /P, /M, /QRP, etc.)
        clean_call = self._clean_callsign(callsign)
        
        # Load CTY data once and cache it (much faster than querying per callsign)
        if self._cty_data is None:
            self._cty_data = self.session.query(CTYData).all()
        
        # Try progressive prefix matching (longest to shortest)
        for length in range(min(len(clean_call), 6), 0, -1):
            prefix = clean_call[:length]
            
            # Check cached CTY data
            for entity in self._cty_data:
                if prefix in entity.prefixes:
                    info = {
                        'continent': entity.continent,
                        'country_name': entity.country_name,
                        'dxcc_code': entity.dxcc_code,
                        'cq_zone': entity.cq_zone,
                        'itu_zone': entity.itu_zone,
                        'primary_prefix': entity.primary_prefix
                    }
                    self._cache[callsign] = info
                    return info
        
        # Not found
        return None
    
    def get_continent(self, callsign: str) -> str:
        """
        Get continent code for a callsign.
        
        Args:
            callsign: The callsign
            
        Returns:
            Continent code (SA, NA, EU, AS, AF, OC) or empty string if not found
        """
        info = self.lookup_callsign(callsign)
        return info['continent'] if info else ''
    
    def is_south_american(self, callsign: str) -> bool:
        """
        Check if a callsign is from South America.
        
        Args:
            callsign: The callsign
            
        Returns:
            True if South American, False otherwise
        """
        return self.get_continent(callsign) == 'SA'
    
    def _clean_callsign(self, callsign: str) -> str:
        """
        Clean callsign by removing portable indicators and special characters.
        
        Args:
            callsign: Raw callsign
            
        Returns:
            Cleaned callsign
        """
        # Remove common suffixes
        call = callsign.upper()
        
        # Remove /P, /M, /QRP, /MM, etc.
        if '/' in call:
            parts = call.split('/')
            # Use the longest part (usually the callsign)
            call = max(parts, key=len)
        
        return call
