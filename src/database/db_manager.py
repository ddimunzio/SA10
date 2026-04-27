"""
Database initialization and management utilities

This module provides functions to create, initialize, and manage the database.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager for handling connections and sessions
    """

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database manager

        Args:
            database_url: SQLAlchemy database URL or file path (for SQLite)
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url
        self.echo = echo

        # Convert file path to SQLite URL if needed
        if not database_url.startswith('sqlite') and not '://' in database_url:
            # Assume it's a file path for SQLite
            database_url = f'sqlite:///{database_url}'
            self.database_url = database_url

        # Special handling for SQLite
        if database_url.startswith('sqlite'):
            self.engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
            # Performance + correctness pragmas applied on every new connection
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                # Referential integrity
                cursor.execute("PRAGMA foreign_keys=ON")
                # WAL mode: writers don't block readers, much faster for bulk writes
                cursor.execute("PRAGMA journal_mode=WAL")
                # NORMAL: flush only at critical checkpoints — safe with WAL,
                # dramatically faster than the default FULL (one fsync per commit)
                cursor.execute("PRAGMA synchronous=NORMAL")
                # 64 MB in-memory page cache (default is ~2 MB)
                cursor.execute("PRAGMA cache_size=-65536")
                # Store temp tables / indices in memory
                cursor.execute("PRAGMA temp_store=MEMORY")
                # 5-second busy timeout so concurrent threads wait instead of fail
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.close()
        else:
            self.engine = create_engine(database_url, echo=echo)

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_all_tables(self):
        """Create all tables in the database"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_all_tables(self):
        """Drop all tables from the database"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")

    def reset_database(self):
        """Drop and recreate all tables"""
        logger.info("Resetting database...")

        # For SQLite, use direct connection to avoid locking issues
        if self.database_url.startswith('sqlite'):
            import sqlite3
            # Extract db path from URL
            db_path = self.database_url.replace('sqlite:///', '')

            # Dispose of all SQLAlchemy connections first
            self.engine.dispose()

            # Use raw SQLite connection to drop tables
            try:
                conn = sqlite3.connect(db_path, timeout=5.0)
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = OFF")
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")

                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error dropping tables: {e}")
                raise
        else:
            # For other databases, use SQLAlchemy
            self.engine.dispose()
            self.drop_all_tables()

        # Recreate tables
        self.create_all_tables()
        logger.info("Database reset complete")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup

        Usage:
            with db_manager.get_session() as session:
                # Use session
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_session_maker(self):
        """Get the session maker for dependency injection"""
        return self.SessionLocal


def init_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """
    Initialize database and create tables

    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to echo SQL statements

    Returns:
        DatabaseManager instance
    """
    db_manager = DatabaseManager(database_url, echo=echo)
    db_manager.create_all_tables()
    return db_manager


def populate_reference_data(session: Session):
    """
    Populate reference tables with initial data

    Args:
        session: Database session
    """
    from .models import CTYData

    logger.info("Populating reference data...")

    # Note: CTYData table will be populated from cty.dat file
    # This is now handled by a separate cty.dat parser module
    # The CTYData table structure is designed to handle the full cty.dat format

    # Check if CTY data is already populated
    if session.query(CTYData).count() > 0:
        logger.info("CTY data already populated")
    else:
        logger.info("CTY data table is empty. Use the cty.dat import functionality to populate it.")
        logger.info("The CTYData table is designed to be populated from the official cty.dat file")
        logger.info("which provides comprehensive DXCC entity and prefix information.")

    session.commit()
    logger.info("Reference data check completed")

