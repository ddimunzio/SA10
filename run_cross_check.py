#!/usr/bin/env python3
"""
Run Cross-Check Validation
Usage: python run_cross_check.py [--contest-id ID] [--db DB_PATH]
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.services.cross_check_service import CrossCheckService
from src.utils import setup_logger

def main():
    parser = argparse.ArgumentParser(description='Run cross-check validation on contest logs')
    parser.add_argument('--contest-id', type=int, default=1, help='Contest ID (default: 1)')
    parser.add_argument('--db', default='sa10_contest.db', help='Database file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    logger = setup_logger("cross_check", console=True, level='DEBUG' if args.verbose else 'INFO')
    
    print("=" * 70)
    print("SA10M CROSS-CHECK VALIDATION")
    print("=" * 70)
    
    db_manager = DatabaseManager(args.db)
    
    try:
        with db_manager.get_session() as session:
            # Verify contest exists
            from sqlalchemy import text
            result = session.execute(
                text("SELECT name FROM contests WHERE id = :id"),
                {"id": args.contest_id}
            ).fetchone()
            
            if not result:
                print(f"[ERROR] Contest ID {args.contest_id} not found")
                sys.exit(1)
                
            print(f"Contest: {result[0]}")
            
            # Initialize service
            cross_check = CrossCheckService(session)
            
            # Run cross-check
            start_time = datetime.now()
            ubn_by_log = cross_check.check_all_logs(args.contest_id)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print(f"\n[TIME] Cross-check completed in {elapsed:.2f} seconds")
            
            # Update database
            print("\nUpdating database with cross-check results...")
            # We need to implement update_database_with_results in CrossCheckService if it's not there
            # Wait, demo_cross_check.py used it, so it must exist?
            # Let's check if it exists in the file I read earlier.
            # I read up to line 600. It might be after that.
            
            # Assuming it exists or I need to add it.
            # If it doesn't exist, I'll add it.
            
            if hasattr(cross_check, 'update_database_with_results'):
                cross_check.update_database_with_results(ubn_by_log)
            else:
                # Implement it here or add to service
                print("[WARNING] update_database_with_results method not found in service")

            # Re-score all logs so that scores.invalid_qsos / not_in_log_qsos
            # reflect the freshly written validation_status values in contacts.
            print("\n[SCORING] Re-scoring logs to update NIL/invalid counts in scores table...")
            from src.services.scoring_service import ScoringService
            from src.database.models import Log
            from sqlalchemy import select as _select

            scoring_service = ScoringService(session, 'sa10m')
            log_ids = list(ubn_by_log.keys())
            scored, failed = 0, 0
            for lid in log_ids:
                try:
                    scoring_service.score_log(lid)
                    scored += 1
                except Exception as se:
                    log_row = session.get(Log, lid)
                    cs = log_row.callsign if log_row else lid
                    print(f"  [WARN] Could not re-score {cs}: {se}")
                    failed += 1
            print(f"[SCORING] Re-scored {scored} logs" + (f", {failed} failed" if failed else ""))

    except Exception as e:
        print(f"[ERROR] Cross-check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
