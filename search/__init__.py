"""
Advanced search functionality for transcripts
"""

from .search_manager import SearchManager, SearchResult, SearchQuery
from .search_index import SearchIndex, DocumentIndex
from .query_parser import QueryParser, ParsedQuery
from .filters import FilterEngine, SearchFilter
from .integration import SearchIntegration, create_search_integration

__all__ = [
    'SearchManager',
    'SearchResult',
    'SearchQuery',
    'SearchIndex',
    'DocumentIndex',
    'QueryParser',
    'ParsedQuery',
    'FilterEngine',
    'SearchFilter',
    'SearchIntegration',
    'create_search_integration'
]

# Optional Streamlit UI components (only import if Streamlit is available)
try:
    from .search_ui import SearchUI, render_search_page
    __all__.extend(['SearchUI', 'render_search_page'])
except ImportError:
    # Streamlit not available, skip UI components
    pass