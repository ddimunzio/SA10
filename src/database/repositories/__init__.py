"""
Database repositories for data access layer
"""

from .log_repository import LogRepository
from .contact_repository import ContactRepository

__all__ = [
    'LogRepository',
    'ContactRepository',
]


