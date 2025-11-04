"""
Database layer - data persistence abstracted from implementation details.
"""

from .repository import Repository
from .sqlite_repository import SQLiteRepository
from .schema import init_database

__all__ = ['Repository', 'SQLiteRepository', 'init_database']
