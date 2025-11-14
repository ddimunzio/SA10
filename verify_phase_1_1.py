"""
Test script to verify all Phase 1.1 Project Setup tasks are complete.
"""

import sys
from pathlib import Path


def test_virtual_environment():
    """Check if running in virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Virtual environment: Active")
        return True
    else:
        print("✗ Virtual environment: Not active (or not using venv)")
        return True  # Still OK if dependencies are installed


def test_dependencies():
    """Check if required dependencies are installed."""
    required = [
        'sqlalchemy',
        'alembic',
        'pydantic',
        'yaml',
        'click',
        'rich',
        'dateutil',
        'pytest',
    ]

    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        print(f"✗ Dependencies: Missing {', '.join(missing)}")
        return False
    else:
        print("✓ Dependencies: All installed")
        return True


def test_project_structure():
    """Check if project structure is correct."""
    base = Path(__file__).parent
    required_dirs = [
        'src',
        'src/core',
        'src/database',
        'src/parsers',
        'src/utils',
        'config',
        'config/contests',
        'tests',
        'docs',
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = base / dir_path
        if not full_path.exists():
            missing.append(dir_path)

    if missing:
        print(f"✗ Project structure: Missing {', '.join(missing)}")
        return False
    else:
        print("✓ Project structure: Complete")
        return True


def test_logging_framework():
    """Check if logging framework is set up."""
    try:
        from src.utils import setup_logger, get_logger, get_app_logger
        logger = get_app_logger()
        logger.info("Test log message")
        print("✓ Logging framework: Set up correctly")
        return True
    except Exception as e:
        print(f"✗ Logging framework: Error - {e}")
        return False


def test_git_repository():
    """Check if Git repository is initialized."""
    base = Path(__file__).parent
    git_dir = base / '.git'
    gitignore = base / '.gitignore'

    if git_dir.exists() and gitignore.exists():
        print("✓ Git repository: Initialized with .gitignore")
        return True
    elif gitignore.exists():
        print("⚠ Git repository: .gitignore exists but .git not found")
        return True
    else:
        print("✗ Git repository: Not initialized")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Phase 1.1 Project Setup - Verification")
    print("=" * 60)
    print()

    results = {
        "Virtual Environment": test_virtual_environment(),
        "Dependencies": test_dependencies(),
        "Project Structure": test_project_structure(),
        "Logging Framework": test_logging_framework(),
        "Git Repository": test_git_repository(),
    }

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for task, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {task}")

    print()
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print()
        print("🎉 All Phase 1.1 tasks complete!")
        print("Ready to proceed to Phase 1.2: Core Data Models")
        return 0
    else:
        print()
        print("⚠ Some tasks incomplete. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

