"""
Rules Engine - Apply contest rules to contacts.

This module applies contest rules to evaluate contacts, calculate points,
identify multipliers, and determine duplicates.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from .rules_loader import ContestRules, ScoringRule, ScoringCondition, MultiplierRule
import re


class Contact:
    """Represents a single contact/QSO."""

    def __init__(
        self,
        timestamp: datetime,
        callsign: str,
        band: str,
        mode: str,
        frequency: int,
        rst_sent: str,
        rst_received: str,
        exchange_sent: Dict[str, str],
        exchange_received: Dict[str, str],
        operator_info: Optional[Dict[str, Any]] = None
    ):
        self.timestamp = timestamp
        self.callsign = callsign
        self.band = band
        self.mode = mode
        self.frequency = frequency
        self.rst_sent = rst_sent
        self.rst_received = rst_received
        self.exchange_sent = exchange_sent
        self.exchange_received = exchange_received
        self.operator_info = operator_info or {}

        # Calculated fields (set by RulesEngine)
        self.points = 0          # Effective points (0 for invalid/duplicate)
        self.raw_points = 0      # Points the QSO would earn if valid (for reporting)
        self.is_duplicate = False
        self.is_multiplier = False
        self.multiplier_types: List[str] = []
        self.validation_errors: List[str] = []


class RulesEngine:
    """Apply contest rules to contacts and calculate scores."""

    def __init__(self, rules: ContestRules, operator_info: Dict[str, Any], callsign_lookup=None):
        """
        Initialize the rules engine.

        Args:
            rules: The contest rules to apply
            operator_info: Information about the operator station
                          (callsign, continent, dxcc, cq_zone, etc.)
            callsign_lookup: Optional CallsignLookupService for continent lookup
        """
        self.rules = rules
        self.operator_info = operator_info
        self.callsign_lookup = callsign_lookup

        # Track worked multipliers per band+mode
        # Key format: "band_mode" (e.g., "10m_CW", "10m_SSB")
        self.worked_prefixes_per_band_mode: Dict[str, Set[str]] = {}
        self.worked_zones_per_band_mode: Dict[str, Set[str]] = {}
        
        # Legacy tracking for contest-wide (kept for backward compatibility)
        self.worked_prefixes: Set[str] = set()
        self.worked_zones_per_band: Dict[str, Set[str]] = {}

        # Track worked callsigns for duplicate detection
        self.worked_calls: Dict[str, List[Contact]] = {}

    def process_contact(self, contact: Contact) -> Contact:
        """
        Process a contact through the rules engine.

        Args:
            contact: The contact to process

        Returns:
            The contact with calculated points and multiplier flags
        """
        # Check if contact is invalid based on validation errors
        is_invalid = len(contact.validation_errors) > 0

        # Check for duplicates
        contact.is_duplicate = self._is_duplicate(contact)

        # Always compute the raw point value (used for penalty reporting)
        contact.raw_points = self._calculate_points(contact)

        # Effective points: 0 for duplicates or invalid contacts
        if contact.is_duplicate or is_invalid:
            contact.points = 0
        else:
            contact.points = contact.raw_points

        # Check multipliers
        if not contact.is_duplicate and not is_invalid:
            contact.is_multiplier, contact.multiplier_types = self._check_multipliers(contact)

        # Record this contact
        self._record_contact(contact)

        return contact

    def _is_duplicate(self, contact: Contact) -> bool:
        """
        Check if contact is a duplicate based on rules.

        Args:
            contact: The contact to check

        Returns:
            True if duplicate, False otherwise
        """
        dup_type = self.rules.validation.duplicate_window.type

        if dup_type == 'none':
            return False

        # Get previous contacts with this callsign
        if contact.callsign not in self.worked_calls:
            return False

        prev_contacts = self.worked_calls[contact.callsign]

        for prev in prev_contacts:
            is_dup = False

            if dup_type == 'contest':
                # Any previous contact with this call is a duplicate
                is_dup = True

            elif dup_type == 'band':
                # Duplicate if same band
                is_dup = (prev.band == contact.band)

            elif dup_type == 'mode':
                # Duplicate if same mode
                is_dup = (prev.mode == contact.mode)

            elif dup_type == 'band_mode':
                # Duplicate if same band AND mode
                is_dup = (prev.band == contact.band and prev.mode == contact.mode)

            if is_dup:
                return True

        return False

    def _calculate_points(self, contact: Contact) -> int:
        """
        Calculate points for a contact based on scoring rules.

        Args:
            contact: The contact to score

        Returns:
            Point value for this contact
        """
        # Evaluate each scoring rule in order
        for rule in self.rules.scoring.points:
            if self._evaluate_conditions(rule.conditions, contact):
                return rule.value

        # No rule matched - default to 0
        return 0

    def _evaluate_conditions(
        self,
        conditions: List[ScoringCondition],
        contact: Contact
    ) -> bool:
        """
        Evaluate if all conditions are met for a contact.

        Args:
            conditions: List of conditions to check
            contact: The contact to evaluate

        Returns:
            True if all conditions are met
        """
        for condition in conditions:
            if not self._evaluate_condition(condition, contact):
                return False
        return True

    def _evaluate_condition(
        self,
        condition: ScoringCondition,
        contact: Contact
    ) -> bool:
        """
        Evaluate a single condition.

        Args:
            condition: The condition to evaluate
            contact: The contact to check

        Returns:
            True if condition is met
        """
        cond_type = condition.type

        # Same DXCC
        if cond_type == 'same_dxcc':
            contact_dxcc = self._get_dxcc(contact.callsign)
            operator_dxcc = self.operator_info.get('dxcc')
            
            # If DXCC codes not available, compare by country name
            if contact_dxcc is None or operator_dxcc is None:
                contact_country = self._get_country(contact.callsign)
                operator_country = self.operator_info.get('country_name', '')
                return contact_country == operator_country and contact_country != ''
            
            return contact_dxcc == operator_dxcc

        # Different DXCC
        elif cond_type == 'different_dxcc':
            contact_dxcc = self._get_dxcc(contact.callsign)
            operator_dxcc = self.operator_info.get('dxcc')
            
            # If DXCC codes not available, compare by country name
            if contact_dxcc is None or operator_dxcc is None:
                contact_country = self._get_country(contact.callsign)
                operator_country = self.operator_info.get('country_name', '')
                return contact_country != operator_country or contact_country == ''
            
            return contact_dxcc != operator_dxcc

        # Operator continent
        elif cond_type == 'operator_continent':
            operator_continent = self.operator_info.get('continent', '')
            if condition.value.startswith('!'):
                # Negation
                return operator_continent != condition.value[1:]
            return operator_continent == condition.value

        # Contact continent
        elif cond_type == 'contact_continent':
            contact_continent = self._get_continent(contact.callsign, contact)
            if condition.value.startswith('!'):
                # Negation
                return contact_continent != condition.value[1:]
            return contact_continent == condition.value

        # Operator zone
        elif cond_type == 'operator_zone':
            operator_zone = str(self.operator_info.get('cq_zone', ''))
            if isinstance(condition.values, list):
                return operator_zone in condition.values
            elif condition.value and condition.value.startswith('!'):
                # Negation - check if NOT in list
                excluded = condition.value[1:].split(',')
                return operator_zone not in excluded
            return operator_zone == str(condition.value)

        # Callsign suffix (e.g., /MM, /AM)
        elif cond_type == 'callsign_suffix':
            operator_call = self.operator_info.get('callsign', '')
            if isinstance(condition.values, list):
                return any(operator_call.endswith(suffix) for suffix in condition.values)
            return operator_call.endswith(condition.value)

        # Contact callsign suffix
        elif cond_type == 'contact_callsign_suffix':
            if isinstance(condition.values, list):
                return any(contact.callsign.endswith(suffix) for suffix in condition.values)
            return contact.callsign.endswith(condition.value)

        # Default: unknown condition type
        return False

    def _check_multipliers(self, contact: Contact) -> Tuple[bool, List[str]]:
        """
        Check if contact provides new multipliers.

        Args:
            contact: The contact to check

        Returns:
            Tuple of (is_new_multiplier, list_of_multiplier_types)
        """
        is_mult = False
        mult_types = []

        for mult_rule in self.rules.scoring.multipliers:
            if self._is_new_multiplier(contact, mult_rule):
                is_mult = True
                mult_types.append(mult_rule.type)
                self._record_multiplier(contact, mult_rule)

        return (is_mult, mult_types)
    
    def _get_band_mode_key(self, contact: Contact) -> str:
        """Get the band+mode key for per_band_mode tracking."""
        return f"{contact.band}_{contact.mode}"

    def _is_new_multiplier(self, contact: Contact, mult_rule: MultiplierRule) -> bool:
        """
        Check if contact is a new multiplier of given type.

        Args:
            contact: The contact to check
            mult_rule: The multiplier rule

        Returns:
            True if this is a new multiplier
        """
        mult_type = mult_rule.type
        scope = mult_rule.scope

        # WPX Prefix
        if mult_type == 'wpx_prefix':
            prefix = self._extract_wpx_prefix(contact.callsign)
            
            if scope == 'per_band_mode':
                key = self._get_band_mode_key(contact)
                if key not in self.worked_prefixes_per_band_mode:
                    self.worked_prefixes_per_band_mode[key] = set()
                return prefix not in self.worked_prefixes_per_band_mode[key]
            elif scope == 'contest':
                return prefix not in self.worked_prefixes

        # CQ Zone
        elif mult_type == 'cq_zone':
            zone = contact.exchange_received.get('cq_zone', '')
            # Must be a valid CQ zone number (1-40); skip non-numeric values like "MG"
            try:
                zone_num = int(zone)
                if not (1 <= zone_num <= 40):
                    return False
            except (ValueError, TypeError):
                return False

            if scope == 'per_band_mode':
                key = self._get_band_mode_key(contact)
                if key not in self.worked_zones_per_band_mode:
                    self.worked_zones_per_band_mode[key] = set()
                return zone not in self.worked_zones_per_band_mode[key]
            elif scope == 'per_band':
                band = contact.band
                if band not in self.worked_zones_per_band:
                    self.worked_zones_per_band[band] = set()
                return zone not in self.worked_zones_per_band[band]
            elif scope == 'contest':
                # Track all zones across all bands
                all_zones = set()
                for zones in self.worked_zones_per_band.values():
                    all_zones.update(zones)
                return zone not in all_zones

        return False

    def _record_multiplier(self, contact: Contact, mult_rule: MultiplierRule):
        """Record that this multiplier has been worked."""
        mult_type = mult_rule.type
        scope = mult_rule.scope

        if mult_type == 'wpx_prefix':
            prefix = self._extract_wpx_prefix(contact.callsign)
            
            if scope == 'per_band_mode':
                key = self._get_band_mode_key(contact)
                if key not in self.worked_prefixes_per_band_mode:
                    self.worked_prefixes_per_band_mode[key] = set()
                self.worked_prefixes_per_band_mode[key].add(prefix)
            
            # Always update legacy contest-wide tracking
            self.worked_prefixes.add(prefix)

        elif mult_type == 'cq_zone':
            zone = contact.exchange_received.get('cq_zone', '')
            # Only record valid CQ zone numbers (1-40)
            try:
                zone_num = int(zone)
                if not (1 <= zone_num <= 40):
                    return
            except (ValueError, TypeError):
                return

            if scope == 'per_band_mode':
                key = self._get_band_mode_key(contact)
                if key not in self.worked_zones_per_band_mode:
                    self.worked_zones_per_band_mode[key] = set()
                self.worked_zones_per_band_mode[key].add(zone)

            # Always update per-band tracking (for backward compatibility)
            band = contact.band
            if band not in self.worked_zones_per_band:
                self.worked_zones_per_band[band] = set()
            self.worked_zones_per_band[band].add(zone)

    def _record_contact(self, contact: Contact):
        """Record contact in worked list."""
        if contact.callsign not in self.worked_calls:
            self.worked_calls[contact.callsign] = []
        self.worked_calls[contact.callsign].append(contact)

    def _extract_wpx_prefix(self, callsign: str) -> str:
        """
        Extract WPX prefix from callsign.

        WPX prefix rules:
        - For callsigns starting with a letter: prefix through first digit
        - For callsigns starting with a digit: prefix through first digit plus following letters

        Examples:
            W1AW -> W1
            K3LR -> K3
            LU3DRP -> LU3
            CE7VP -> CE7
            9A3YT -> 9A3
            4U1ITU -> 4U1

        Args:
            callsign: The callsign to extract from

        Returns:
            The WPX prefix
        """
        # Remove any /portable indicators
        base_call = callsign.split('/')[0]

        # Find first digit
        match = re.search(r'\d', base_call)
        if not match:
            return base_call  # No digit found, return whole call

        digit_pos = match.start()

        # If callsign starts with a digit, include following letters until next digit
        if digit_pos == 0:
            prefix = base_call[0]  # Start with the digit
            for i in range(1, len(base_call)):
                if base_call[i].isalpha():
                    prefix += base_call[i]
                elif base_call[i].isdigit():
                    prefix += base_call[i]
                    break
                else:
                    break
        else:
            # Standard case: prefix through first digit
            prefix = base_call[:digit_pos + 1]

        return prefix

    def _get_dxcc(self, callsign: str) -> Optional[int]:
        """
        Get DXCC entity for a callsign using CTY data.

        Args:
            callsign: The callsign

        Returns:
            DXCC entity code or None
        """
        # Use callsign lookup service if available
        if self.callsign_lookup:
            info = self.callsign_lookup.lookup_callsign(callsign)
            if info:
                return info.get('dxcc_code')
        
        # Fallback to simple mapping if no lookup service available
        prefix = callsign[:2]
        simple_mapping = {
            'LU': 100,  # Argentina
            'CE': 112,  # Chile
            'PY': 108,  # Brazil
            'W': 291,   # USA
            'K': 291,   # USA
            'G': 223,   # England
            'EA': 281,  # Spain
        }
        return simple_mapping.get(prefix)

    def _get_continent(self, callsign: str, contact: Optional[Contact] = None) -> str:
        """
        Get continent for a callsign using CTY data.
        
        Uses cached continent from contact if available (much faster).

        Args:
            callsign: The callsign
            contact: Optional Contact object with cached continent

        Returns:
            Continent code (SA, NA, EU, AS, AF, OC) or empty string if not found
        """
        # Use cached continent if available (fastest)
        if contact and hasattr(contact, '_cached_continent'):
            return contact._cached_continent
        
        # Use lookup service if available
        if self.callsign_lookup:
            return self.callsign_lookup.get_continent(callsign)
        
        # Fallback to simple mapping if no lookup service available
        prefix = callsign[:2]
        simple_mapping = {
            'LU': 'SA', 'CE': 'SA', 'PY': 'SA', 'CX': 'SA', 'ZW': 'SA',
            'PT': 'SA', 'PP': 'SA', 'PU': 'SA', 'LT': 'SA', 'AY': 'SA',
            'W': 'NA', 'K': 'NA', 'N': 'NA',
            'G': 'EU', 'EA': 'EU', 'DL': 'EU',
        }
        return simple_mapping.get(prefix, '')

    def _get_country(self, callsign: str) -> str:
        """
        Get country name for a callsign using CTY data.

        Args:
            callsign: The callsign

        Returns:
            Country name or empty string if not found
        """
        # Use callsign lookup service if available
        if self.callsign_lookup:
            info = self.callsign_lookup.lookup_callsign(callsign)
            if info:
                return info.get('country_name', '')
        
        return ''

    def calculate_final_score(self, contacts: List[Contact]) -> Dict[str, Any]:
        """
        Calculate final score from all contacts.
        
        SA10M uses per-mode scoring: Sum of (mode_points × mode_multipliers) for each mode.
        Each zone and prefix counts once per band+mode combination.

        Args:
            contacts: List of all contacts

        Returns:
            Dictionary with score breakdown
        """
        total_qsos = len(contacts)
        invalid_qsos = sum(1 for c in contacts if len(c.validation_errors) > 0)
        not_in_log_qsos = sum(1 for c in contacts if 'not_in_log' in c.validation_errors)
        valid_qsos = sum(1 for c in contacts if not c.is_duplicate and len(c.validation_errors) == 0)
        duplicate_qsos = sum(1 for c in contacts if c.is_duplicate)
        
        # Calculate per-mode scores (SA10M formula)
        # Get all unique modes from actual contacts
        unique_modes = set(c.mode for c in contacts if not c.is_duplicate)
        
        mode_scores = {}
        final_score = 0
        
        for mode in unique_modes:
            mode_contacts = [c for c in contacts if c.mode == mode and not c.is_duplicate]
            mode_points = sum(c.points for c in mode_contacts)
            
            # Count multipliers for this mode across all bands
            mode_wpx_mults = set()
            mode_zone_mults = set()
            
            for key, prefixes in self.worked_prefixes_per_band_mode.items():
                if key.endswith(f'_{mode}'):
                    mode_wpx_mults.update(prefixes)
            
            for key, zones in self.worked_zones_per_band_mode.items():
                if key.endswith(f'_{mode}'):
                    mode_zone_mults.update(zones)
            
            mode_total_mults = len(mode_wpx_mults) + len(mode_zone_mults)
            mode_score = mode_points * mode_total_mults
            final_score += mode_score
            
            mode_scores[mode] = {
                'qsos': len(mode_contacts),
                'points': mode_points,
                'wpx_multipliers': len(mode_wpx_mults),
                'zone_multipliers': len(mode_zone_mults),
                'total_multipliers': mode_total_mults,
                'score': mode_score
            }
        
        # Legacy counts for backward compatibility
        total_points = sum(c.points for c in contacts)
        wpx_mults = len(self.worked_prefixes)
        all_zones = set()
        for zones in self.worked_zones_per_band.values():
            all_zones.update(zones)
        total_zone_mults = len(all_zones)
        total_multipliers = wpx_mults + total_zone_mults

        # Calculate per-band breakdown for statistics
        band_scores = {}
        final_score = 0
        
        # Check if we should use the generic formula
        use_generic_formula = True
        if self.rules.scoring.final_score.formula == "TOTAL_POINTS * (MULT1 + MULT2)":
             final_score = total_points * total_multipliers
             use_generic_formula = False # We calculated it directly
        elif self.rules.scoring.final_score.formula == "SUM_OF_MODE_SCORES":
             # Sum of mode scores
             final_score = sum(m['score'] for m in mode_scores.values())
             use_generic_formula = False
        
        for band in self.rules.contest.bands:
            band_contacts = [c for c in contacts if c.band == band and not c.is_duplicate]
            band_points = sum(c.points for c in band_contacts)
            band_zones = len(self.worked_zones_per_band.get(band, set()))
            
            # For statistics, we might want to show band score
            # Assuming WPX applies to band if contest-wide
            band_wpx = wpx_mults # Simplified assumption for single band contest
            band_total_mults = band_wpx + band_zones
            band_score = band_points * band_total_mults

            band_scores[band] = {
                'qsos': len(band_contacts),
                'points': band_points,
                'zones_on_band': band_zones,
                'score': band_score
            }
            
            if use_generic_formula and self.rules.scoring.final_score.formula == "BY_BAND":
                 final_score += band_score

        return {
            'total_qsos': total_qsos,
            'valid_qsos': valid_qsos,
            'duplicate_qsos': duplicate_qsos,
            'invalid_qsos': invalid_qsos,
            'not_in_log_qsos': not_in_log_qsos,
            'total_points': total_points,
            'wpx_multipliers': wpx_mults,
            'zone_multipliers': total_zone_mults,
            'total_multipliers': total_multipliers,
            'band_scores': band_scores,
            'mode_scores': mode_scores,
            'all_zones': sorted(all_zones),
            'final_score': final_score
        }


if __name__ == '__main__':
    # Test the rules engine
    from .rules_loader import load_sa10m_rules

    print("Loading SA10M rules...")
    rules = load_sa10m_rules()

    # Create operator info
    operator_info = {
        'callsign': 'LU1ABC',
        'continent': 'SA',
        'dxcc': 100,
        'cq_zone': 13
    }

    print(f"Operator: {operator_info['callsign']} (CQ Zone {operator_info['cq_zone']})")

    # Create rules engine
    engine = RulesEngine(rules, operator_info)

    # Test contacts
    test_contacts = [
        Contact(
            timestamp=datetime.now(),
            callsign='W1AW',
            band='10m',
            mode='SSB',
            frequency=28500,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        ),
        Contact(
            timestamp=datetime.now(),
            callsign='K3LR',
            band='10m',
            mode='SSB',
            frequency=28510,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '5'}
        ),
        Contact(
            timestamp=datetime.now(),
            callsign='CE7VP',
            band='10m',
            mode='SSB',
            frequency=28520,
            rst_sent='59',
            rst_received='59',
            exchange_sent={'cq_zone': '13'},
            exchange_received={'cq_zone': '12'}
        ),
    ]

    print("\n--- Processing Contacts ---")
    processed = []
    for contact in test_contacts:
        result = engine.process_contact(contact)
        processed.append(result)

        wpx = engine._extract_wpx_prefix(contact.callsign)
        dup = "DUP" if result.is_duplicate else ""
        mult = "MULT" if result.is_multiplier else ""
        print(f"{contact.callsign:10s} [{wpx:4s}] Zone {contact.exchange_received.get('cq_zone'):2s} = "
              f"{result.points} pts {mult} {dup}")

    print("\n--- Final Score ---")
    score = engine.calculate_final_score(processed)
    print(f"Valid QSOs: {score['valid_qsos']}")
    print(f"Total Points: {score['total_points']}")
    print(f"WPX Multipliers: {score['wpx_multipliers']}")
    print(f"Zone Multipliers: {score['zone_multipliers']}")
    print(f"Final Score: {score['final_score']}")

