"""
Search providers for different backends
"""

from .sqlite_search import SQLiteSearchProvider
from .whoosh_search import WhooshSearchProvider

__all__ = [
    'SQLiteSearchProvider',
    'WhooshSearchProvider'
]