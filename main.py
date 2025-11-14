#!/usr/bin/env python3
"""
Ham Radio Contest Results Calculator
Main entry point for the application.
"""

import sys
from pathlib import Path

from src.utils import setup_logger, get_logger


def main():
    """Main entry point."""
    # Set up logging
    logger = setup_logger("ham_contest", console=True)
    logger.info("Starting Ham Radio Contest Results Calculator")

    print("=" * 60)
    print("Ham Radio Contest Results Calculator")
    print("=" * 60)
    print()
    print("Version: 0.1.0")
    print("Status: Under Development")
    print()
    print("This application will calculate contest results based on")
    print("configurable rules and store them in a database.")
    print()
    print("See IMPLEMENTATION_PLAN.md for development roadmap.")
    print()
    print("Current Project Structure:")
    print("  ✓ Project skeleton created")
    print("  ✓ Virtual environment configured")
    print("  ✓ Dependencies installed")
    print("  ✓ Logging framework set up")
    print("  ✓ Git repository initialized")
    print("  ✓ SA10M contest rules configured")
    print("  ⏳ Core models (Phase 1 - Next)")
    print("  ⏳ Rules engine (Phase 2)")
    print("  ⏳ Log parsers (Phase 3)")
    print("  ⏳ Scoring engine (Phase 4)")
    print()
    print("Next Steps:")
    print("  1. Review IMPLEMENTATION_PLAN.md")
    print("  2. Begin Phase 1.2: Core Models implementation")
    print()
    print("73! 📻")
    print("=" * 60)

    logger.info("Application startup complete")


if __name__ == "__main__":
    main()

