"""
Database layer - data persistence abstracted from implementation details.
"""

from .repository import Repository
from .schema import init_database

__all__ = ['Repository', 'init_database']
