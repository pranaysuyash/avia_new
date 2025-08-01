# Advanced Search Module

This module provides powerful full-text search capabilities for transcripts using SQLite FTS5.

## Features

- **Full-text search** with relevance ranking
- **Query syntax support**:
  - Exact phrases: `"tech support"`
  - Boolean operators: `support OR development`
  - Exclusions: `-revenue` or `NOT revenue`
  - Required terms: `+important`
- **Advanced filters**:
  - Speaker: `speaker:John`
  - Tags: `tag:business`
  - Entity types: `entity:PERSON`
  - Date ranges: `date:2024-01`, `after:yesterday`, `before:2024-12-31`
  - Language: `lang:en`
  - Confidence: `confidence:>0.8`
- **Search features**:
  - Snippet highlighting
  - Faceted search results
  - Search suggestions
  - Saved searches
  - Search history
  - Export results (JSON/CSV)

## Usage

### Basic Usage

```python
from search import SearchIntegration

# Initialize search
search = SearchIntegration()

# Index a transcript
transcript = {
    "id": "meeting_001",
    "title": "Team Meeting",
    "text": "Discussion about project goals...",
    "segments": [...],
    "entities": [...],
    "metadata": {
        "tags": ["meeting", "planning"],
        "language": "en"
    }
}

await search.index_transcription_result(transcript)

# Perform a search
results = search.search("project goals")
print(f"Found {results['total_count']} results")
```

### Advanced Queries

```python
# Search with filters
results = search.search(
    "revenue",
    filters={
        'speakers': ['John', 'Mary'],
        'tags': ['business'],
        'date_range': {
            'start': '2024-01-01',
            'end': '2024-12-31'
        }
    }
)

# Complex query with operators
results = search.search('support OR development -bug tag:urgent')

# Exact phrase search
results = search.search('"customer satisfaction"')
```

### Using the Search Manager

```python
from search import SearchManager, SearchQuery

# Initialize manager
manager = SearchManager()

# Create a search query
query = SearchQuery(
    query="performance metrics",
    filters={'entity_types': ['PERCENT', 'MONEY']},
    options={
        'limit': 25,
        'highlight': True,
        'include_facets': True
    }
)

# Execute search
result = await manager.search(query)

# Access results
for doc in result.results:
    print(f"{doc['title']}: {doc['content_snippet']}")

# Check facets
for facet_type, values in result.facets.items():
    print(f"\n{facet_type}:")
    for value, count in values.items():
        print(f"  - {value}: {count}")
```

### Streamlit UI

```python
from search import render_search_page

# In your Streamlit app
render_search_page()
```

### Batch Indexing

```python
# Index multiple transcripts
transcripts = [...]  # List of transcript dictionaries
await search.index_batch(transcripts)

# Index from directory
results = await search.index_directory(
    "/path/to/transcripts",
    pattern="*.json"
)
```

## Query Syntax Reference

### Text Operators
- `word1 word2` - Both words must appear (implicit AND)
- `word1 OR word2` - Either word must appear
- `"exact phrase"` - Exact phrase match
- `-excluded` - Exclude documents with this word
- `+required` - Word must appear

### Filter Syntax
- `speaker:name` - Filter by speaker
- `tag:tagname` - Filter by tag
- `entity:PERSON` - Filter by entity type
- `date:2024-01-15` - Specific date
- `after:2024-01-01` - After date
- `before:2024-12-31` - Before date
- `lang:en` - Language filter
- `confidence:>0.8` - Minimum confidence

### Special Filters
- `date:today` - Today's documents
- `date:yesterday` - Yesterday's documents
- `date:week` - Last 7 days
- `date:month` - Last 30 days

## API Reference

### SearchIntegration

Main integration class for search functionality.

#### Methods

- `index_transcription_result(result)` - Index a single transcript
- `index_from_file(file_path)` - Index from JSON file
- `index_directory(directory_path, pattern)` - Index all files in directory
- `search(query, filters, options)` - Perform search
- `update_transcript_metadata(id, metadata)` - Update indexed metadata
- `delete_transcript(id)` - Remove from index

### SearchManager

Advanced search management with caching and history.

#### Methods

- `search(query)` - Execute search query
- `save_search(name, query, filters)` - Save search for reuse
- `get_saved_searches()` - Retrieve saved searches
- `get_search_history(limit)` - Get recent searches
- `export_results(results, format)` - Export results as JSON/CSV

### QueryParser

Parse complex search queries.

#### Methods

- `parse(query)` - Parse query into components
- `suggest_query(partial, history)` - Get query suggestions

## Database Schema

The search index uses SQLite with FTS5 virtual tables:

- `documents` - Main document storage
- `documents_fts` - FTS5 virtual table for searching
- `saved_searches` - Saved search queries
- `search_history` - Search history tracking

## Performance Tips

1. **Batch indexing** - Use `index_batch()` for multiple documents
2. **Caching** - Results are cached for 5 minutes by default
3. **Pagination** - Use limit/offset for large result sets
4. **Selective indexing** - Only index searchable fields
5. **Regular maintenance** - Periodically optimize the database

## Examples

See `examples/search_example.py` for complete usage examples.