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

    def check_all_logs(self, contest_id: int, progress_callback=None) -> Dict[int, List[UBNEntry]]:
        """
        Run complete cross-check on all logs for a contest

        Args:
            contest_id: Contest ID to check
            progress_callback: Optional callback function for progress updates

        Returns:
            Dictionary mapping log_id to list of UBN entries
        """
        print(f"\n[CROSSCHECK] Starting cross-check for contest ID {contest_id}...")

        # Get all submitted callsigns first
        submitted_calls = self._get_submitted_callsigns(contest_id)
        print(f"   Found {len(submitted_calls)} submitted logs")

        # Step 1: Find Not-in-Log contacts
        print("\n[STEP 1/3] Detecting Not-in-Log (NIL) contacts...")
        nil_entries = self._find_not_in_log(contest_id)
        print(f"   Found {len(nil_entries)} NIL contacts")

        # Step 2: Find Unique calls
        print("\n[STEP 2/3] Detecting UNIQUE calls...")
        unique_entries = self._find_unique_calls(contest_id, submitted_calls)
        print(f"   Found {len(unique_entries)} unique calls")

        # Step 3: Find Busted calls
        print("\n[STEP 3/3] Detecting BUSTED calls...")
        busted_entries = self._find_busted_calls(contest_id, submitted_calls)
        print(f"   Found {len(busted_entries)} busted calls")

        # Organize by log_id
        ubn_by_log: Dict[int, List[UBNEntry]] = {}
        for entry in nil_entries + unique_entries + busted_entries:
            if entry.log_id not in ubn_by_log:
                ubn_by_log[entry.log_id] = []
            ubn_by_log[entry.log_id].append(entry)

        # Calculate statistics
        self._calculate_statistics(contest_id, ubn_by_log)

        print(f"\n[SUCCESS] Cross-check complete!")
        print(f"   Total logs with issues: {len(ubn_by_log)}")

        return ubn_by_log

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
                AND c.is_valid = 1
                AND c.validation_status != 'duplicate'
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
        Find busted (incorrectly copied) callsigns using Levenshtein distance

        Strategy:
        1. Get all unique worked calls that didn't submit
        2. For each, find similar submitted callsigns (distance 1-2)
        3. Check if the suggested call has a QSO with the logging station at approximately the same time
        4. Only report as busted if the suggested station has the reciprocal QSO
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

                        for suggested_call, similarity in busted_mapping[worked_call]:
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
                                best_similarity = similarity
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
                                    best_zone_match_similarity = similarity

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
                zone_tally[zone_key][str(exchange_sent).strip()] += 1

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
        logged_zone = logged_exchange.strip().lstrip('0') or '0'
        try:
            zone_num = int(logged_zone)
            if not (1 <= zone_num <= 40):
                return False
        except ValueError:
            return False
        dominant = dominant_zone_cache.get((callsign, band, mode))
        if not dominant:
            return False
        station_zone = str(dominant).strip().lstrip('0') or '0'
        return station_zone == logged_zone

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

        logged_zone = logged_exchange.strip().lstrip('0') or '0'

        # Validate it is a plausible CQ zone number
        try:
            zone_num = int(logged_zone)
            if not (1 <= zone_num <= 40):
                return False
        except ValueError:
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

        station_zone = str(row[0]).strip().lstrip('0') or '0'
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
        Update contact records with cross-check results

        Sets validation_status and validation_notes for NIL and BUSTED contacts
        """
        print("\n[DATABASE] Updating database with cross-check results...")

        update_count = 0
        for log_id, entries in ubn_by_log.items():
            for entry in entries:
                if entry.ubn_type == UBNType.NOT_IN_LOG:
                    query = text("""
                        UPDATE contacts 
                        SET 
                            validation_status = 'not_in_log',
                            validation_notes = :notes,
                            updated_at = :now
                        WHERE id = :contact_id
                    """)
                    self.session.execute(query, {
                        "contact_id": entry.contact_id,
                        "notes": f"Not-in-log: {entry.worked_callsign} has no record of this QSO",
                        "now": datetime.utcnow()
                    })
                    update_count += 1

                elif entry.ubn_type == UBNType.BUSTED:
                    query = text("""
                        UPDATE contacts 
                        SET 
                            validation_status = 'invalid_callsign',
                            validation_notes = :notes,
                            is_valid = 0,
                            updated_at = :now
                        WHERE id = :contact_id
                    """)
                    notes = f"Busted call: {entry.worked_callsign} (should be: {entry.suggested_call}?)"
                    if entry.other_station_has_qso:
                        notes += " - Other station has QSO with correct call"

                    self.session.execute(query, {
                        "contact_id": entry.contact_id,
                        "notes": notes,
                        "now": get_utc_now()
                    })
                    update_count += 1

                elif entry.ubn_type == UBNType.UNIQUE:
                    query = text("""
                        UPDATE contacts 
                        SET 
                            validation_status = 'unique_call',
                            validation_notes = :notes,
                            updated_at = :now
                        WHERE id = :contact_id
                        AND (validation_status IS NULL OR validation_status NOT IN ('busted_call', 'invalid_callsign'))
                    """)
                    self.session.execute(query, {
                        "contact_id": entry.contact_id,
                        "notes": f"Unique call: {entry.worked_callsign} did not submit a log",
                        "now": get_utc_now()
                    })
                    update_count += 1

        # Update log status to 'validated' for all cross-checked logs
        from src.database.models import ContestStatus
        log_ids = list(ubn_by_log.keys())
        if log_ids:
            placeholders = ','.join([f':lid_{i}' for i in range(len(log_ids))])
            lp = {f'lid_{i}': lid for i, lid in enumerate(log_ids)}
            self.session.execute(
                text(f"UPDATE logs SET status = 'VALIDATED' WHERE id IN ({placeholders})"),
                lp
            )

        self.session.commit()
        print(f"   Updated {update_count} contact records")

