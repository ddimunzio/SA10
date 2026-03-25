#!/usr/bin/env python3
"""
Contest Management Utility

Simple script to create and manage contests in the database.
Usage:
    # Create a new contest
    python manage_contest.py create "SA10M 2025" sa10m-2025 "2025-03-08 00:00" "2025-03-09 23:59"

    # List all contests
    python manage_contest.py list

    # Show contest details
    python manage_contest.py show 1

    # Delete a contest
    python manage_contest.py delete 1
"""

import sys
import argparse
from datetime import datetime
from typing import Optional

from src.database.db_manager import DatabaseManager
from src.database.models import Contest


def create_contest(db_manager: DatabaseManager, name: str, slug: str,
                  start_date: str, end_date: str, rules_file: str = None) -> Optional[int]:
    """Create a new contest."""

    # Parse dates
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
    except ValueError as e:
        print(f"Error: Invalid date format. Use YYYY-MM-DD HH:MM")
        print(f"       {e}")
        return None

    # Default rules file
    if rules_file is None:
        rules_file = "config/contests/sa10m.yaml"

    with db_manager.get_session() as session:
        # Check if slug already exists
        existing = session.query(Contest).filter(Contest.slug == slug).first()
        if existing:
            print(f"Error: Contest with slug '{slug}' already exists (ID: {existing.id})")
            return None

        contest = Contest(
            name=name,
            slug=slug,
            start_date=start_dt,
            end_date=end_dt,
            rules_file=rules_file
        )

        session.add(contest)
        session.commit()

        print(f"[OK] Contest created successfully!")
        print(f"  ID: {contest.id}")
        print(f"  Name: {contest.name}")
        print(f"  Slug: {contest.slug}")
        print(f"  Start: {contest.start_date}")
        print(f"  End: {contest.end_date}")
        print(f"  Rules: {contest.rules_file}")

        return contest.id


def list_contests(db_manager: DatabaseManager):
    """List all contests."""
    with db_manager.get_session() as session:
        contests = session.query(Contest).order_by(Contest.start_date.desc()).all()

        if not contests:
            print("No contests found in database.")
            return

        print(f"\n{'ID':<5} {'Name':<30} {'Slug':<20} {'Start Date':<20}")
        print("=" * 80)

        for contest in contests:
            print(f"{contest.id:<5} {contest.name:<30} {contest.slug:<20} "
                  f"{contest.start_date.strftime('%Y-%m-%d %H:%M'):<20}")

        print(f"\nTotal: {len(contests)} contest(s)")


def show_contest(db_manager: DatabaseManager, contest_id: int):
    """Show detailed contest information."""
    with db_manager.get_session() as session:
        contest = session.query(Contest).filter(Contest.id == contest_id).first()

        if not contest:
            print(f"Error: Contest ID {contest_id} not found")
            return

        print("\n" + "=" * 70)
        print(f"Contest Details (ID: {contest.id})")
        print("=" * 70)
        print(f"Name:       {contest.name}")
        print(f"Slug:       {contest.slug}")
        print(f"Start Date: {contest.start_date}")
        print(f"End Date:   {contest.end_date}")
        print(f"Rules File: {contest.rules_file}")
        print(f"Created:    {contest.created_at}")
        print(f"Updated:    {contest.updated_at}")

        # Count logs
        log_count = len(contest.logs)
        print(f"\nLogs Submitted: {log_count}")

        if log_count > 0:
            print("\nCallsigns:")
            for log in contest.logs[:10]:  # Show first 10
                print(f"  - {log.callsign}")
            if log_count > 10:
                print(f"  ... and {log_count - 10} more")


def delete_contest(db_manager: DatabaseManager, contest_id: int):
    """Delete a contest (and all associated logs)."""
    with db_manager.get_session() as session:
        contest = session.query(Contest).filter(Contest.id == contest_id).first()

        if not contest:
            print(f"Error: Contest ID {contest_id} not found")
            return

        log_count = len(contest.logs)

        print(f"\nWARNING: You are about to delete:")
        print(f"  Contest: {contest.name} (ID: {contest.id})")
        print(f"  This will also delete {log_count} log(s) and all their contacts!")

        confirm = input("\nType 'yes' to confirm: ")

        if confirm.lower() != 'yes':
            print("Cancelled.")
            return

        session.delete(contest)
        session.commit()

        print(f"[OK] Contest deleted successfully")


def main():
    parser = argparse.ArgumentParser(
        description='Manage contests in the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--db',
        default='sa10_contest.db',
        help='Database file path (default: sa10_contest.db)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new contest')
    create_parser.add_argument('name', help='Contest name (e.g., "SA10M 2025")')
    create_parser.add_argument('slug', help='Contest slug (e.g., "sa10m-2025")')
    create_parser.add_argument('start_date', help='Start date and time (YYYY-MM-DD HH:MM)')
    create_parser.add_argument('end_date', help='End date and time (YYYY-MM-DD HH:MM)')
    create_parser.add_argument('--rules', help='Path to rules YAML file')

    # List command
    list_parser = subparsers.add_parser('list', help='List all contests')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show contest details')
    show_parser.add_argument('contest_id', type=int, help='Contest ID')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a contest')
    delete_parser.add_argument('contest_id', type=int, help='Contest ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize database
    db_manager = DatabaseManager(args.db)
    db_manager.create_all_tables()

    # Execute command
    if args.command == 'create':
        create_contest(db_manager, args.name, args.slug, args.start_date,
                      args.end_date, args.rules)

    elif args.command == 'list':
        list_contests(db_manager)

    elif args.command == 'show':
        show_contest(db_manager, args.contest_id)

    elif args.command == 'delete':
        delete_contest(db_manager, args.contest_id)

    return 0


if __name__ == '__main__':
    sys.exit(main())

