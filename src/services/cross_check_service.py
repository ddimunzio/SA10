"""
Cross-checking Service for Contest Log Validation

Uses pure SQL queries to perform fast cross-log validation:
- Not-in-Log (NIL) detection
- Busted call detection
- Unique call identification
- Bidirectional QSO matching

Based on Phase 4.3 implementation plan.
"""

from bisect import bisect_left, insort
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from dataclasses import dataclass
from enum import Enum
import Levenshtein

from ..utils import extract_cq_zone, load_master_scp

# ---------------------------------------------------------------------------
# Morse code table and mode-aware callsign similarity
# ---------------------------------------------------------------------------
_MORSE: Dict[str, str] = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',   'E': '.',
    'F': '..-.',  'G': '--.',   'H': '....',  'I': '..',    'J': '.---',
    'K': '-.-',   'L': '.-..',  'M': '--',    'N': '-.',    'O': '---',
    'P': '.--.',  'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',  'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
}


def _morse_char_cost(c1: str, c2: str) -> float:
    """
    Substitution cost for two callsign characters in CW context.
    Returns 0.0 for identical characters and up to 1.0 for completely
    unrelated Morse sequences.  Pairs that share most of their Morse
    elements (e.g. E/I, T/N, A/N, D/B) receive a fractional cost so
    they are treated as more likely confusions than random swaps.
    """
    c1, c2 = c1.upper(), c2.upper()
    if c1 == c2:
        return 0.0
    m1 = _MORSE.get(c1)
    m2 = _MORSE.get(c2)
    if m1 is None or m2 is None:
        return 1.0
    ldist = Levenshtein.distance(m1, m2)
    return ldist / max(len(m1), len(m2))


def callsign_similarity(worked: str, suggested: str, mode: str) -> float:
    """
    Mode-aware callsign similarity in [0, 1] (higher = more similar).

    CW  — weighted Levenshtein where each substitution cost equals the
          normalised Morse edit distance between the two characters.
          Morse-similar pairs (E/I, T/N, D/B, …) get a lower cost and
          therefore a higher overall similarity score.
    PH  — Jaro-Winkler, which emphasises prefix matches and is a good
          fit for callsign phonetic copying errors.
    other — plain Levenshtein ratio (unchanged behaviour).
    """
    w, s = worked.upper(), suggested.upper()
    if w == s:
        return 1.0

    m = (mode or "").upper()

    if m in ("PH", "SSB", "FM"):
        return Levenshtein.jaro_winkler(w, s)

    if m == "CW":
        n, slen = len(w), len(s)
        if n == 0 or slen == 0:
            return 0.0
        # Standard Levenshtein DP with Morse-weighted substitution costs.
        prev = [float(j) for j in range(slen + 1)]
        for i in range(1, n + 1):
            curr = [float(i)] + [0.0] * slen
            for j in range(1, slen + 1):
                cost = _morse_char_cost(w[i - 1], s[j - 1])
                curr[j] = min(
                    prev[j] + 1.0,        # deletion
                    curr[j - 1] + 1.0,    # insertion
                    prev[j - 1] + cost,   # substitution
                )
            prev = curr
        return 1.0 - prev[slen] / (n + slen)

    # Fallback: plain Levenshtein ratio
    return Levenshtein.ratio(w, s)


def get_utc_now() -> datetime:
    """Get current UTC time in a timezone-aware way"""
    try:
        return datetime.now(timezone.utc)
    except AttributeError:
        # Fallback for older Python versions
        return datetime.utcnow()


def parse_datetime(dt) -> datetime:
    """Parse datetime from various formats (SQLite compatibility)"""
    if isinstance(dt, datetime):
        return dt
    if isinstance(dt, str):
        # Try common formats
        for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
            try:
                return datetime.strptime(dt, fmt)
            except ValueError:
                continue
        # If all else fails, try ISO format
        return datetime.fromisoformat(dt.replace('Z', '+00:00'))
    return dt


class UBNType(str, Enum):
    """Type of UBN entry"""
    UNIQUE = "unique"
    BUSTED = "busted"
    NOT_IN_LOG = "nil"


@dataclass
class UBNEntry:
    """Single UBN entry for a contact"""
    contact_id: int
    log_id: int
    log_callsign: str
    worked_callsign: str
    timestamp: datetime
    band: str
    mode: str
    frequency: int
    ubn_type: UBNType

    # Exchange information
    rst_sent: str
    exchange_sent: str
    rst_received: str
    exchange_received: str

    # For BUSTED calls
    suggested_call: Optional[str] = None
    similarity_score: Optional[float] = None
    other_station_has_qso: bool = False

    # For NIL
    other_log_id: Optional[int] = None
    time_difference_seconds: Optional[int] = None


@dataclass
class CrossCheckStats:
    """Statistics from cross-checking"""
    total_contacts: int
    valid_contacts: int
    unique_count: int
    busted_count: int
    nil_count: int
    matched_count: int

    def error_rate(self) -> float:
        """Calculate overall error rate"""
        if self.total_contacts == 0:
            return 0.0
        errors = self.busted_count + self.nil_count
        return (errors / self.total_contacts) * 100


class CrossCheckService:
    """
    Service for cross-checking contest logs using SQL queries

    Time tolerance: ±5 minutes (0.003472 days in JULIANDAY)
    """

    TIME_TOLERANCE_DAYS = 0.003472  # 5 minutes in days
    LEVENSHTEIN_THRESHOLD = 2     # Max edit distance for busted calls
    LEVENSHTEIN_MIN_RATIO  = 0.65  # Minimum similarity ratio (rejects short-call false positives)

    def __init__(self, session: Session):
        self.session = session
        self.stats = {}

    def _reset_cross_check_results(self, contest_id: int) -> None:
        """
        Reset all contacts that were previously written by the cross-check
        (invalid_callsign, not_in_log, unique_call) back to 'valid' / is_valid=1
        so that a fresh run starts from a clean state.

        Contacts that were originally valid (not flagged by import validation)
        are the only ones touched; duplicates and import-time errors are left alone.
        """
        query = text("""
            UPDATE contacts
            SET
                validation_status = 'valid',
                validation_notes  = NULL,
                is_valid          = 1,
                updated_at        = :now
            WHERE log_id IN (
                SELECT id FROM logs WHERE contest_id = :contest_id
            )
            AND validation_status IN ('invalid_callsign', 'not_in_log', 'unique_call')
        """)
        result = self.session.execute(query, {"contest_id": contest_id, "now": get_utc_now()})
        self.session.flush()
        print(f"   Reset {result.rowcount} contact(s) from previous cross-check run")

    def check_all_logs(self, contest_id: int, progress_callback=None,
                       master_calls_file: Optional[str] = None) -> Dict[int, List[UBNEntry]]:
        """
        Run complete cross-check on all logs for a contest

        Args:
            contest_id: Contest ID to check
            progress_callback: Optional callback function for progress updates
            master_calls_file: Optional path to MASTER.SCP for unique-call verification

        Returns:
            Dictionary mapping log_id to list of UBN entries
        """
        print(f"\n[CROSSCHECK] Starting cross-check for contest ID {contest_id}...")

        # Reset any results written by a previous cross-check run so that
        # stale invalid_callsign / not_in_log / unique_call flags do not
        # interfere with the new run (e.g. a wrongly-busted call that is
        # now correctly treated as unique would stay is_valid=0 forever
        # without this reset).
        print("\n[RESET] Clearing previous cross-check results...")
        self._reset_cross_check_results(contest_id)

        # Get all submitted callsigns first
        submitted_calls = self._get_submitted_callsigns(contest_id)
        print(f"   Found {len(submitted_calls)} submitted logs")

        # Load master SCP if provided
        master_calls = load_master_scp(master_calls_file) if master_calls_file else frozenset()
        if master_calls:
            print(f"   Loaded {len(master_calls)} callsigns from MASTER.SCP")
        elif master_calls_file:
            print(f"   [WARN] MASTER.SCP not found — corroboration-only check will run")

        # Step 1: Find Not-in-Log contacts
        print("\n[STEP 1/3] Detecting Not-in-Log (NIL) contacts...")
        if progress_callback:
            progress_callback(0, 3)
        nil_entries = self._find_not_in_log(contest_id)
        print(f"   Found {len(nil_entries)} NIL contacts")

        # Step 2: Find Unique calls
        print("\n[STEP 2/3] Detecting UNIQUE calls...")
        if progress_callback:
            progress_callback(1, 3)
        unique_entries = self._find_unique_calls(contest_id, submitted_calls)
        print(f"   Found {len(unique_entries)} unique calls")

        # Step 2b: Reclassify suspicious unique calls as BUSTED
        reclassified = self._apply_unique_call_filter(unique_entries, master_calls)
        if reclassified:
            print(f"   Reclassified {reclassified} unique call(s) as BUSTED "
                  f"(not in SCP + no corroboration)")

        # Step 3: Find Busted calls
        print("\n[STEP 3/3] Detecting BUSTED calls...")
        if progress_callback:
            progress_callback(2, 3)
        busted_entries = self._find_busted_calls(contest_id, submitted_calls)
        print(f"   Found {len(busted_entries)} busted calls")

        # Merge all entries, deduplicating by contact_id.
        # A contact may appear in both unique_entries (reclassified as BUSTED
        # with no suggestion) and busted_entries (found with a real suggestion).
        # When that happens, keep the entry that has a suggested_call (busted_entries
        # wins over the no-suggestion reclassified entry).
        seen: Dict[int, UBNEntry] = {}
        for entry in nil_entries + unique_entries + busted_entries:
            existing = seen.get(entry.contact_id)
            if existing is None:
                seen[entry.contact_id] = entry
            else:
                # Prefer the entry with an actual suggested call
                if entry.suggested_call is not None and existing.suggested_call is None:
                    seen[entry.contact_id] = entry

        ubn_by_log: Dict[int, List[UBNEntry]] = {}
        for entry in seen.values():
            if entry.log_id not in ubn_by_log:
                ubn_by_log[entry.log_id] = []
            ubn_by_log[entry.log_id].append(entry)

        # Calculate statistics
        self._calculate_statistics(contest_id, ubn_by_log)

        print(f"\n[SUCCESS] Cross-check complete!")
        print(f"   Total logs with issues: {len(ubn_by_log)}")
        if progress_callback:
            progress_callback(3, 3)

        return ubn_by_log

    def _apply_unique_call_filter(
        self,
        unique_entries: List[UBNEntry],
        master_calls: frozenset,
    ) -> int:
        """
        Reclassify unique calls that are likely fabricated as BUSTED.

        A unique call is considered suspicious — and reclassified to
        UBNType.BUSTED with no suggested replacement — when it fails BOTH:
          1. It is NOT present in the provided MASTER.SCP callsign set.
          2. It is NOT corroborated: no log OTHER than the one being evaluated
             also worked the same callsign.

        A call that satisfies either condition is left as UNIQUE (trusted).

        Args:
            unique_entries: List of UNIQUE UBNEntry objects (modified in place).
            master_calls:   frozenset of uppercase SCP callsigns (may be empty).

        Returns:
            Number of entries reclassified as BUSTED.
        """
        if not unique_entries:
            return 0

        # Build corroboration index: call → set of log_ids that worked it
        call_to_logs: Dict[str, Set[int]] = defaultdict(set)
        for entry in unique_entries:
            call_to_logs[entry.worked_callsign.upper()].add(entry.log_id)

        reclassified = 0
        for entry in unique_entries:
            call_upper = entry.worked_callsign.upper()
            in_scp = bool(master_calls) and call_upper in master_calls
            corroborated = len(call_to_logs[call_upper] - {entry.log_id}) >= 1

            if not in_scp and not corroborated:
                entry.ubn_type = UBNType.BUSTED
                entry.suggested_call = None  # No known correct call
                reclassified += 1

        return reclassified

    def _get_submitted_callsigns(self, contest_id: int) -> Set[str]:
        """Get all callsigns that submitted logs"""
        query = text("""
            SELECT DISTINCT callsign 
            FROM logs 
            WHERE contest_id = :contest_id
        """)
        result = self.session.execute(query, {"contest_id": contest_id})
        return {row[0] for row in result}

    def _find_not_in_log(self, contest_id: int) -> List[UBNEntry]:
        """
        Find contacts where reciprocal QSO is missing (Not-in-Log)

        Optimized approach:
        1. Load all contacts for this contest into memory
        2. Build hash maps for fast lookup
        3. Check each contact for reciprocal QSO
        """
        # Get all contacts for this contest
        query = text("""
            SELECT 
                c.id as contact_id,
                c.log_id,
                l.callsign as log_callsign,
                c.call_received,
                c.qso_datetime,
                c.band,
                c.mode,
                c.frequency,
                c.rst_sent,
                c.exchange_sent,
                c.rst_received,
                c.exchange_received,
                c.is_valid,
                c.validation_status
            FROM contacts c
            INNER JOIN logs l ON c.log_id = l.id
            WHERE l.contest_id = :contest_id
            ORDER BY l.id, c.qso_datetime
        """)

        result = self.session.execute(query, {"contest_id": contest_id})
        all_contacts = list(result)
        
        print(f"   Loaded {len(all_contacts):,} contacts into memory")
        
        # Build a map of callsign -> log_id for submitted logs
        # Also track checklog IDs — their contacts help validate others but they
        # receive no NIL/BUSTED/UNIQUE penalties themselves.
        log_query = text("""
            SELECT id, callsign, category_operator
            FROM logs WHERE contest_id = :contest_id
        """)
        log_result = self.session.execute(log_query, {"contest_id": contest_id})
        submitted_logs = {}
        checklog_ids: set = set()
        for row in log_result:
            submitted_logs[row.callsign] = row.id
            if (row.category_operator or "").upper() == "CHECKLOG":
                checklog_ids.add(row.id)
        print(f"   Check logs (not penalised): {len(checklog_ids)}")
        
        # Build hash map for fast reciprocal QSO lookup
        # Key: (log_id, call_received, band, mode, time_bucket)
        # time_bucket groups times into 1-minute windows
        qso_map = {}
        # Secondary map for fuzzy matching: (log_id, band, mode, time_bucket)
        qso_time_map = {}

        for row in all_contacts:
            # Parse datetime
            dt = parse_datetime(row.qso_datetime)
            # Create time bucket (round to minute)
            time_bucket = dt.replace(second=0, microsecond=0)
            
            # Add entry for current minute
            key = (row.log_id, row.call_received, row.band, row.mode, time_bucket)
            if key not in qso_map:
                qso_map[key] = []
            qso_map[key].append(row)

            # Add to time map
            time_key = (row.log_id, row.band, row.mode, time_bucket)
            if time_key not in qso_time_map:
                qso_time_map[time_key] = []
            qso_time_map[time_key].append(row)
        
        print(f"   Built hash map with {len(qso_map):,} entries")
        
        # Now check each contact for reciprocal QSO.
        #
        # Two-pass strategy to suppress "phantom duplicate" NILs:
        #   A phantom duplicate occurs when a log has two entries for the same
        #   station/band/mode (one is a logging error, the other is real).  The
        #   import marks the second entry is_valid=False (duplicate), so only the
        #   first — which has no match — would be flagged NIL.  That is unfair
        #   because the operator DID make the contact.
        #
        # Pass 1: iterate ALL contacts (including is_valid=False ones) to build
        #   confirmed_combos: set of (log_id, call_received, band, mode) that have
        #   at least one confirmed reciprocal match anywhere in the log.
        #   Only is_valid entries go into pending_nils.
        # Pass 2: suppress NILs whose combo already appears in confirmed_combos.
        confirmed_combos: set = set()
        pending_nils = []  # (row, dt, other_log_id)
        checked = 0

        for row in all_contacts:
            # Determine whether this row should be a NIL candidate
            is_nil_candidate = (row.is_valid == 1 and row.validation_status != 'duplicate')

            # Check if the worked station submitted a log
            other_log_id = submitted_logs.get(row.call_received)
            if not other_log_id:
                # Worked station didn't submit - will be caught as UNIQUE
                continue

            # Look for reciprocal QSO
            dt = parse_datetime(row.qso_datetime)
            time_bucket = dt.replace(second=0, microsecond=0)

            # Check if reciprocal QSO exists within ±5 minutes
            found = False
            from datetime import timedelta

            # Check range -5 to +5 minutes
            for time_offset in range(-5, 6):
                check_time = time_bucket + timedelta(minutes=time_offset)
                key = (other_log_id, row.log_callsign, row.band, row.mode, check_time)

                if key in qso_map:
                    # Found potential matches, verify time tolerance
                    for other_row in qso_map[key]:
                        other_dt = parse_datetime(other_row.qso_datetime)
                        time_diff = abs((dt - other_dt).total_seconds())
                        if time_diff <= 300:  # 5 minutes = 300 seconds
                            found = True
                            break
                if found:
                    break

            if not found:
                # Try to find fuzzy match (other station busted our call)
                for time_offset in range(-5, 6):
                    check_time = time_bucket + timedelta(minutes=time_offset)
                    time_key = (other_log_id, row.band, row.mode, check_time)

                    if time_key in qso_time_map:
                        for other_row in qso_time_map[time_key]:
                            # Check time tolerance
                            other_dt = parse_datetime(other_row.qso_datetime)
                            time_diff = abs((dt - other_dt).total_seconds())
                            if time_diff > 300:
                                continue

                            # Check callsign similarity
                            dist = Levenshtein.distance(other_row.call_received, row.log_callsign)
                            if dist <= self.LEVENSHTEIN_THRESHOLD:
                                found = True
                                break
                    if found:
                        break

            combo = (row.log_id, row.call_received, row.band, row.mode)
            if found:
                confirmed_combos.add(combo)
            elif is_nil_candidate and row.log_id not in checklog_ids:
                pending_nils.append((row, dt, other_log_id))

            if is_nil_candidate:
                checked += 1
            if checked % 10000 == 0 and checked > 0:
                print(f"   Checked {checked:,} / {len(all_contacts):,} contacts...")

        # Pass 2: emit NIL only when the log has NO confirmed QSO with that station
        # on the same band/mode.  If a confirmed match exists elsewhere in the log,
        # this unmatched entry is a phantom duplicate — penalising it as NIL would
        # be unfair since the operator did make the contact.
        entries = []
        suppressed = 0
        for row, dt, other_log_id in pending_nils:
            combo = (row.log_id, row.call_received, row.band, row.mode)
            if combo in confirmed_combos:
                suppressed += 1
                continue
            entries.append(UBNEntry(
                contact_id=row.contact_id,
                log_id=row.log_id,
                log_callsign=row.log_callsign,
                worked_callsign=row.call_received,
                timestamp=dt,
                band=row.band,
                mode=row.mode,
                frequency=row.frequency,
                ubn_type=UBNType.NOT_IN_LOG,
                rst_sent=row.rst_sent,
                exchange_sent=row.exchange_sent,
                rst_received=row.rst_received,
                exchange_received=row.exchange_received,
                other_log_id=other_log_id
            ))

        if suppressed:
            print(f"   Suppressed {suppressed} NIL(s) where a confirmed QSO exists "
                  f"with the same station on the same band/mode (phantom duplicates)")

        return entries

    def _find_unique_calls(self, contest_id: int, submitted_calls: Set[str]) -> List[UBNEntry]:
        """
        Find calls that appear in logs but didn't submit

        These are calls that:
        - Appear in contacts
        - Are not in the submitted_calls set
        - May be valid (station didn't submit) or busted
        """
        query = text("""
            SELECT 
                c.id as contact_id,
                c.log_id,
                l.callsign as log_callsign,
                c.call_received as worked_callsign,
                c.qso_datetime,
                c.band,
                c.mode,
                c.frequency,
                c.rst_sent,
                c.exchange_sent,
                c.rst_received,
                c.exchange_received,
                COUNT(*) OVER (PARTITION BY c.call_received) as times_worked
            FROM contacts c
            INNER JOIN logs l ON c.log_id = l.id
            WHERE 
                l.contest_id = :contest_id
                AND c.validation_status NOT IN ('duplicate', 'invalid', 'out_of_period',
                                                'invalid_band', 'invalid_mode')
                AND UPPER(COALESCE(l.category_operator,'')) != 'CHECKLOG'
            ORDER BY l.callsign, c.qso_datetime
        """)

        result = self.session.execute(query, {"contest_id": contest_id})

        entries = []
        for row in result:
            # Only include if callsign didn't submit
            if row.worked_callsign not in submitted_calls:
                entries.append(UBNEntry(
                    contact_id=row.contact_id,
                    log_id=row.log_id,
                    log_callsign=row.log_callsign,
                    worked_callsign=row.worked_callsign,
                    timestamp=parse_datetime(row.qso_datetime),
                    band=row.band,
                    mode=row.mode,
                    frequency=row.frequency,
                    ubn_type=UBNType.UNIQUE,
                    rst_sent=row.rst_sent,
                    exchange_sent=row.exchange_sent,
                    rst_received=row.rst_received,
                    exchange_received=row.exchange_received
                ))

        return entries

    def _find_busted_calls(self, contest_id: int, submitted_calls: Set[str]) -> List[UBNEntry]:
        """
        Find busted (incorrectly copied) callsigns using mode-aware similarity.

        Strategy:
        1. Get all unique worked calls that didn't submit.
        2. Build a candidate list using Levenshtein distance 1-2 as a coarse filter.
        3. Per contact, re-rank candidates with mode-aware similarity:
              CW  — Morse-weighted edit distance (likely Morse confusions rank higher).
              PH  — Jaro-Winkler (rewards common prefixes).
        4. Accept the top-ranked candidate that has a reciprocal QSO; fall back to
           zone-match for distance-1 candidates when no reciprocal is found.
        """
        # Get all unique non-submitted calls
        query = text("""
            SELECT DISTINCT c.call_received
            FROM contacts c
            INNER JOIN logs l ON c.log_id = l.id
            WHERE l.contest_id = :contest_id
        """)
        result = self.session.execute(query, {"contest_id": contest_id})
        worked_calls = {row[0] for row in result}

        # Find calls that didn't submit
        non_submitted = worked_calls - submitted_calls

        print(f"   Comparing {len(non_submitted)} non-submitted calls against {len(submitted_calls)} submitted calls...")

        # Pre-load all contact data once so busted-call checks use in-memory
        # lookups instead of individual SQL queries (major performance win).
        print("   Pre-loading contact data for fast in-memory lookups...")
        reciprocal_map, dominant_zone_cache = self._build_lookup_caches(contest_id)
        _tolerance_sec = self.TIME_TOLERANCE_DAYS * 86400

        # Find busted calls by comparing with submitted calls
        # Optimize by filtering by first character and length first
        busted_mapping: Dict[str, List[Tuple[str, float]]] = {}

        # Group submitted calls by first character and length for faster matching
        submitted_by_char_len = {}
        for call in submitted_calls:
            if call:
                key = (call[0], len(call))
                if key not in submitted_by_char_len:
                    submitted_by_char_len[key] = []
                submitted_by_char_len[key].append(call)

        checked = 0
        for worked_call in non_submitted:
            similar_calls = []

            # Only compare with calls that could be similar (same first char or similar length)
            candidates = set()
            if worked_call:
                # Same first character
                key = (worked_call[0], len(worked_call))
                candidates.update(submitted_by_char_len.get(key, []))

                # Similar length (±2)
                for length_diff in [-2, -1, 1, 2]:
                    key = (worked_call[0], len(worked_call) + length_diff)
                    candidates.update(submitted_by_char_len.get(key, []))

                # Different first character but same length (for prefix swaps)
                for first_char in set(c[0] for c in submitted_calls if c):
                    if first_char != worked_call[0]:
                        key = (first_char, len(worked_call))
                        candidates.update(submitted_by_char_len.get(key, []))

            for submitted_call in candidates:
                distance = Levenshtein.distance(worked_call, submitted_call)
                if 1 <= distance <= self.LEVENSHTEIN_THRESHOLD:
                    ratio = Levenshtein.ratio(worked_call, submitted_call)
                    if ratio < self.LEVENSHTEIN_MIN_RATIO:
                        continue  # Too dissimilar despite low edit distance
                    similarity = ratio
                    similar_calls.append((submitted_call, similarity))

            if similar_calls:
                # Sort by similarity (highest first)
                similar_calls.sort(key=lambda x: x[1], reverse=True)
                busted_mapping[worked_call] = similar_calls

            checked += 1
            if checked % 100 == 0:
                print(f"   Checked {checked:,} / {len(non_submitted):,} calls for Levenshtein matches...")

        print(f"   Found {len(busted_mapping)} potential busted calls")

        # Now find all contacts with busted calls
        entries = []
        if busted_mapping:
            # Get contacts with these busted calls in batches
            busted_calls_list = list(busted_mapping.keys())
            batch_size = 500  # SQLite has variable limit, keep batches reasonable

            for batch_start in range(0, len(busted_calls_list), batch_size):
                batch_calls = busted_calls_list[batch_start:batch_start + batch_size]
                placeholders = ','.join([f':call_{i}' for i in range(len(batch_calls))])

                query = text(f"""
                    SELECT 
                        c.id as contact_id,
                        c.log_id,
                        l.callsign as log_callsign,
                        c.call_received as worked_callsign,
                        c.qso_datetime,
                        c.band,
                        c.mode,
                        c.frequency,
                        c.rst_sent,
                        c.exchange_sent,
                        c.rst_received,
                        c.exchange_received
                    FROM contacts c
                    INNER JOIN logs l ON c.log_id = l.id
                    WHERE 
                        l.contest_id = :contest_id
                        AND c.validation_status != 'duplicate'
                        AND c.call_received IN ({placeholders})
                        AND UPPER(COALESCE(l.category_operator,'')) != 'CHECKLOG'
                    ORDER BY l.callsign, c.qso_datetime
                """)

                params = {"contest_id": contest_id}
                for i, call in enumerate(batch_calls):
                    params[f'call_{i}'] = call

                result = self.session.execute(query, params)

                # Track which (log_id, suggested_call) pairs have already been used
                # within a short window to prevent the same correct call from being
                # assigned to two different worked_calls in the same log.
                used_suggestion: Dict[tuple, datetime] = {}

                for row in result:
                    worked_call = row.worked_callsign
                    if worked_call in busted_mapping:
                        qso_timestamp = parse_datetime(row.qso_datetime)

                        # Try all similar calls and pick the best one that has reciprocal QSO
                        best_suggestion = None
                        best_similarity = 0
                        has_qso = False

                        # Track best distance-1 zone-match candidate (no reciprocal fallback)
                        best_zone_match_suggestion = None
                        best_zone_match_similarity = 0

                        # Re-rank candidates using mode-aware similarity so that
                        # Morse-plausible (CW) or phonetically-plausible (PH) swaps
                        # are tried before generic edit-distance candidates.
                        mode_ranked = sorted(
                            (
                                (sug, callsign_similarity(worked_call, sug, row.mode))
                                for sug, _ in busted_mapping[worked_call]
                            ),
                            key=lambda x: x[1],
                            reverse=True,
                        )

                        for suggested_call, mode_similarity in mode_ranked:
                            # Guard: a station cannot work itself
                            if suggested_call == row.log_callsign:
                                continue

                            # Guard: the same suggested_call cannot be used twice for the
                            # same log within 10 minutes (one station can't log us twice)
                            dedup_key = (row.log_id, suggested_call)
                            if dedup_key in used_suggestion:
                                prev_ts = used_suggestion[dedup_key]
                                if abs((qso_timestamp - prev_ts).total_seconds()) < 600:
                                    continue

                            edit_distance = Levenshtein.distance(worked_call, suggested_call)

                            # Check if suggested station has QSO with logging station at approximately same time
                            if self._reciprocal_exists_mem(
                                reciprocal_map, suggested_call, row.log_callsign,
                                qso_timestamp, row.band, row.mode, _tolerance_sec
                            ):
                                # Found a match with reciprocal QSO
                                best_suggestion = suggested_call
                                best_similarity = mode_similarity
                                has_qso = True
                                break

                            # Fallback for distance-1: check if the logged exchange zone
                            # matches the most common zone sent by the suggested call.
                            # This catches copies where the other station didn't log us.
                            if edit_distance == 1 and best_zone_match_suggestion is None:
                                if self._zone_match_mem(
                                    dominant_zone_cache, suggested_call,
                                    row.exchange_received, row.band, row.mode
                                ):
                                    best_zone_match_suggestion = suggested_call
                                    best_zone_match_similarity = mode_similarity

                        # Use zone-match fallback only when no reciprocal was found
                        if not has_qso and best_zone_match_suggestion:
                            best_suggestion = best_zone_match_suggestion
                            best_similarity = best_zone_match_similarity

                        if best_suggestion:
                            used_suggestion[(row.log_id, best_suggestion)] = qso_timestamp
                            entries.append(UBNEntry(
                                contact_id=row.contact_id,
                                log_id=row.log_id,
                                log_callsign=row.log_callsign,
                                worked_callsign=worked_call,
                                timestamp=qso_timestamp,
                                band=row.band,
                                mode=row.mode,
                                frequency=row.frequency,
                                ubn_type=UBNType.BUSTED,
                                rst_sent=row.rst_sent,
                                exchange_sent=row.exchange_sent,
                                rst_received=row.rst_received,
                                exchange_received=row.exchange_received,
                                suggested_call=best_suggestion,
                                similarity_score=best_similarity,
                                other_station_has_qso=has_qso
                            ))

                if (batch_start + batch_size) % 2000 == 0:
                    print(f"   Processed {min(batch_start + batch_size, len(busted_calls_list)):,} / {len(busted_calls_list):,} busted calls...")

        return entries

    def _build_lookup_caches(self, contest_id: int):
        """
        Pre-load all contact data for the contest into memory so that
        _find_busted_calls can do O(log n) bisect lookups instead of
        one SQL round-trip per candidate.

        Returns:
            reciprocal_map  – {(log_callsign, call_received, band, mode): sorted [datetime, ...]}
            dominant_zone_cache – {(callsign, band, mode): dominant_exchange_sent_str}
        """
        query = text("""
            SELECT l.callsign, c.call_received, c.band, c.mode,
                   c.qso_datetime, c.exchange_sent
            FROM contacts c
            INNER JOIN logs l ON c.log_id = l.id
            WHERE l.contest_id = :contest_id
        """)

        reciprocal_map: Dict[tuple, list] = defaultdict(list)
        zone_tally: Dict[tuple, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        _skipped = 0
        for row in self.session.execute(query, {"contest_id": contest_id}):
            log_callsign, call_received, band, mode, qso_dt_str, exchange_sent = row
            key = (log_callsign, call_received, band, mode)
            try:
                dt = parse_datetime(qso_dt_str)
                insort(reciprocal_map[key], dt)
            except (ValueError, TypeError) as exc:
                _skipped += 1
                print(
                    f"   [WARN] _build_lookup_caches: skipped unparseable datetime "
                    f"for {log_callsign} -> {call_received} "
                    f"band={band} mode={mode} qso_datetime={qso_dt_str!r}: {exc}"
                )
            if exchange_sent:
                zone_key = (log_callsign, band, mode)
                zone_value = extract_cq_zone(exchange_sent)
                if zone_value is not None:
                    zone_tally[zone_key][zone_value] += 1

        if _skipped:
            print(f"   [WARN] _build_lookup_caches: {_skipped} contact(s) omitted from "
                  f"reciprocal map due to unparseable datetimes (see warnings above).")

        dominant_zone_cache = {
            key: max(counts, key=counts.get)
            for key, counts in zone_tally.items()
        }
        return dict(reciprocal_map), dominant_zone_cache

    @staticmethod
    def _reciprocal_exists_mem(reciprocal_map: dict, log_callsign: str,
                                call_received: str, timestamp: datetime,
                                band: str, mode: str, tolerance_sec: float) -> bool:
        """In-memory equivalent of _check_reciprocal_exists using bisect."""
        times = reciprocal_map.get((log_callsign, call_received, band, mode))
        if not times:
            return False
        pos = bisect_left(times, timestamp)
        for i in (pos - 1, pos):
            if 0 <= i < len(times):
                if abs((times[i] - timestamp).total_seconds()) <= tolerance_sec:
                    return True
        return False

    @staticmethod
    def _zone_match_mem(dominant_zone_cache: dict, callsign: str,
                        logged_exchange: str, band: str, mode: str) -> bool:
        """In-memory equivalent of _check_zone_match using a pre-built cache."""
        if not logged_exchange:
            return False
        logged_zone = extract_cq_zone(logged_exchange)
        if logged_zone is None:
            return False
        dominant = dominant_zone_cache.get((callsign, band, mode))
        if not dominant:
            return False
        return dominant == logged_zone

    def _check_zone_match(self, contest_id: int, callsign: str,
                          logged_exchange: str, band: str, mode: str) -> bool:
        """
        Check if the zone logged for a contact matches what the suggested callsign
        typically sent in this contest.  Used as a distance-1 busted-call fallback
        when no reciprocal QSO exists.

        Normalises both sides by stripping leading zeros before comparing.
        Returns True only if there is exactly one dominant zone for the suggested
        station AND it matches the logged exchange.
        """
        if not logged_exchange:
            return False

        logged_zone = extract_cq_zone(logged_exchange)
        if logged_zone is None:
            return False

        query = text("""
            SELECT c.exchange_sent, COUNT(*) as cnt
            FROM contacts c
            INNER JOIN logs l ON c.log_id = l.id
            WHERE l.contest_id = :contest_id
              AND l.callsign   = :callsign
              AND c.band       = :band
              AND c.mode       = :mode
              AND c.exchange_sent IS NOT NULL
              AND c.exchange_sent != ''
            GROUP BY c.exchange_sent
            ORDER BY cnt DESC
            LIMIT 1
        """)
        row = self.session.execute(query, {
            "contest_id": contest_id,
            "callsign": callsign,
            "band": band,
            "mode": mode,
        }).fetchone()

        if not row:
            return False

        station_zone = extract_cq_zone(row[0])
        return station_zone == logged_zone

    def _check_reciprocal_exists(self, contest_id: int, callsign1: str, callsign2: str,
                                  timestamp: datetime, band: str, mode: str) -> bool:
        """Check if a reciprocal QSO exists between two stations"""
        query = text("""
            SELECT COUNT(*) as count
            FROM contacts c
            INNER JOIN logs l ON c.log_id = l.id
            WHERE 
                l.contest_id = :contest_id
                AND l.callsign = :callsign1
                AND c.call_received = :callsign2
                AND c.band = :band
                AND c.mode = :mode
                AND ABS(JULIANDAY(c.qso_datetime) - JULIANDAY(:timestamp)) < :time_tolerance
        """)

        result = self.session.execute(query, {
            "contest_id": contest_id,
            "callsign1": callsign1,
            "callsign2": callsign2,
            "band": band,
            "mode": mode,
            "timestamp": timestamp,
            "time_tolerance": self.TIME_TOLERANCE_DAYS
        })

        count = result.scalar()
        return count > 0

    def _calculate_statistics(self, contest_id: int, ubn_by_log: Dict[int, List[UBNEntry]]):
        """Calculate statistics for each log"""
        query = text("""
            SELECT 
                l.id as log_id,
                l.callsign,
                COUNT(c.id) as total_contacts,
                SUM(CASE WHEN c.is_valid = 1 AND c.validation_status != 'duplicate' THEN 1 ELSE 0 END) as valid_contacts
            FROM logs l
            LEFT JOIN contacts c ON c.log_id = l.id
            WHERE l.contest_id = :contest_id
            GROUP BY l.id, l.callsign
        """)

        result = self.session.execute(query, {"contest_id": contest_id})

        for row in result:
            log_id = row.log_id
            ubn_entries = ubn_by_log.get(log_id, [])

            unique_count = sum(1 for e in ubn_entries if e.ubn_type == UBNType.UNIQUE)
            busted_count = sum(1 for e in ubn_entries if e.ubn_type == UBNType.BUSTED)
            nil_count = sum(1 for e in ubn_entries if e.ubn_type == UBNType.NOT_IN_LOG)

            self.stats[log_id] = CrossCheckStats(
                total_contacts=row.total_contacts,
                valid_contacts=row.valid_contacts,
                unique_count=unique_count,
                busted_count=busted_count,
                nil_count=nil_count,
                matched_count=row.valid_contacts - unique_count - busted_count - nil_count
            )

    def get_statistics(self, log_id: int) -> Optional[CrossCheckStats]:
        """Get cross-check statistics for a specific log"""
        return self.stats.get(log_id)

    def update_database_with_results(self, ubn_by_log: Dict[int, List[UBNEntry]]):
        """
        Update contact records with cross-check results.

        Collects all per-type params first, then issues a single executemany
        call per update type instead of one SQL round-trip per contact.
        """
        print("\n[DATABASE] Updating database with cross-check results...")

        nil_params:    list = []
        busted_params: list = []
        unique_params: list = []
        now = get_utc_now()

        for entries in ubn_by_log.values():
            for entry in entries:
                if entry.ubn_type == UBNType.NOT_IN_LOG:
                    nil_params.append({
                        "contact_id": entry.contact_id,
                        "notes": f"Not-in-log: {entry.worked_callsign} has no record of this QSO",
                        "now": now,
                    })
                elif entry.ubn_type == UBNType.BUSTED:
                    suggested = entry.suggested_call or "?"
                    notes = f"Busted call: {entry.worked_callsign} (should be: {suggested})"
                    if entry.other_station_has_qso:
                        notes += " - Other station has QSO with correct call"
                    busted_params.append({
                        "contact_id": entry.contact_id,
                        "notes": notes,
                        "now": now,
                    })
                elif entry.ubn_type == UBNType.UNIQUE:
                    unique_params.append({
                        "contact_id": entry.contact_id,
                        "notes": f"Unique call: {entry.worked_callsign} did not submit a log",
                        "now": now,
                    })

        conn = self.session.connection()

        if nil_params:
            conn.execute(
                text("""UPDATE contacts
                         SET validation_status = 'not_in_log',
                             validation_notes  = :notes,
                             updated_at        = :now
                         WHERE id = :contact_id"""),
                nil_params,
            )

        if busted_params:
            conn.execute(
                text("""UPDATE contacts
                         SET validation_status = 'invalid_callsign',
                             validation_notes  = :notes,
                             is_valid          = 0,
                             updated_at        = :now
                         WHERE id = :contact_id"""),
                busted_params,
            )

        if unique_params:
            conn.execute(
                text("""UPDATE contacts
                         SET validation_status = 'unique_call',
                             validation_notes  = :notes,
                             updated_at        = :now
                         WHERE id = :contact_id
                           AND (validation_status IS NULL
                                OR validation_status NOT IN ('busted_call', 'invalid_callsign'))"""),
                unique_params,
            )

        update_count = len(nil_params) + len(busted_params) + len(unique_params)

        # Update log status to 'validated' for all cross-checked logs
        log_ids = list(ubn_by_log.keys())
        if log_ids:
            placeholders = ','.join([f':lid_{i}' for i in range(len(log_ids))])
            lp = {f'lid_{i}': lid for i, lid in enumerate(log_ids)}
            self.session.execute(
                text(f"UPDATE logs SET status = 'VALIDATED' WHERE id IN ({placeholders})"),
                lp,
            )

        self.session.commit()
        print(f"   Updated {update_count} contact records "
              f"({len(nil_params)} NIL, {len(busted_params)} busted, {len(unique_params)} unique)")

    def rebuild_ubn_from_db(self, contest_id: int) -> Dict[int, List["UBNEntry"]]:
        """
        Reconstruct ``ubn_by_log`` from the contact records already stored in
        the database (populated by a previous call to
        ``update_database_with_results``).

        This allows UBN report generation to be run as a standalone step
        without having to re-execute the full cross-check.

        The ``self.stats`` dict is also populated so that
        ``CrossCheckStats`` objects are available for report generation.

        Returns:
            Dict mapping log_id → list of UBNEntry (same structure as
            ``check_all_logs`` returns).
        """
        STATUS_MAP = {
            "not_in_log":       UBNType.NOT_IN_LOG,
            "invalid_callsign": UBNType.BUSTED,
            "unique_call":      UBNType.UNIQUE,
        }

        rows = self.session.execute(
            text("""
                SELECT
                    c.id,
                    c.log_id,
                    l.callsign          AS log_callsign,
                    c.call_received     AS worked_callsign,
                    c.qso_datetime      AS timestamp,
                    c.band,
                    c.mode,
                    COALESCE(c.frequency, 0) AS frequency,
                    c.validation_status,
                    c.validation_notes,
                    COALESCE(c.rst_sent, '')      AS rst_sent,
                    COALESCE(c.exchange_sent, '') AS exchange_sent,
                    COALESCE(c.rst_received, '')  AS rst_received,
                    COALESCE(c.exchange_received,'') AS exchange_received
                FROM contacts c
                JOIN logs     l ON l.id = c.log_id
                WHERE l.contest_id = :contest_id
                  AND c.validation_status IN ('not_in_log','invalid_callsign','unique_call')
                ORDER BY c.log_id, c.qso_datetime
            """),
            {"contest_id": contest_id},
        ).fetchall()

        ubn_by_log: Dict[int, List[UBNEntry]] = {}
        for row in rows:
            ubn_type = STATUS_MAP[row.validation_status]

            # Try to extract suggested call from validation_notes for busted entries
            suggested_call: Optional[str] = None
            if ubn_type == UBNType.BUSTED and row.validation_notes:
                import re as _re
                m = _re.search(r"should be[:\s]+([A-Z0-9/]+)", row.validation_notes or "")
                if m:
                    suggested_call = m.group(1)

            ts = parse_datetime(row.timestamp) if isinstance(row.timestamp, str) else row.timestamp

            entry = UBNEntry(
                contact_id=row.id,
                log_id=row.log_id,
                log_callsign=row.log_callsign,
                worked_callsign=row.worked_callsign,
                timestamp=ts,
                band=row.band,
                mode=row.mode,
                frequency=row.frequency,
                ubn_type=ubn_type,
                rst_sent=row.rst_sent,
                exchange_sent=row.exchange_sent,
                rst_received=row.rst_received,
                exchange_received=row.exchange_received,
                suggested_call=suggested_call,
            )
            ubn_by_log.setdefault(row.log_id, []).append(entry)

        # Rebuild stats so report generation has totals per log
        self._calculate_statistics(contest_id, ubn_by_log)

        print(f"[rebuild_ubn_from_db] Loaded {sum(len(v) for v in ubn_by_log.values())} "
              f"entries across {len(ubn_by_log)} logs from DB")
        return ubn_by_log

