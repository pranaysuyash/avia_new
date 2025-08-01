"""
Integration module for search functionality with main application
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from .search_manager import SearchManager, SearchQuery
from .search_index import DocumentIndex

logger = logging.getLogger(__name__)


class SearchIntegration:
    """Integrates search functionality with the main application"""
    
    def __init__(self, search_index_path: str = "search_index.db"):
        self.search_manager = SearchManager(search_index_path)
        self.logger = logger
        
    async def index_transcription_result(self, result: Dict[str, Any]) -> bool:
        """
        Index a transcription result for searching
        
        Args:
            result: Transcription result containing:
                - id: Unique identifier
                - title: Title or filename
                - text: Full transcript text
                - segments: List of segments with text and metadata
                - entities: Extracted entities
                - language: Detected language
                - metadata: Additional metadata
                
        Returns:
            bool: Success status
        """
        try:
            # Extract required fields
            doc_id = result.get('id', '')
            title = result.get('title', 'Untitled')
            
            # Build content from segments
            segments = result.get('segments', [])
            content_parts = []
            speakers = set()
            
            for segment in segments:
                text = segment.get('text', '').strip()
                if text:
                    content_parts.append(text)
                    
                # Extract speaker info
                speaker = segment.get('speaker')
                if speaker:
                    speakers.add(speaker)
                    
            content = ' '.join(content_parts)
            
            # Extract entities
            entities = result.get('entities', [])
            
            # Extract tags from metadata
            metadata = result.get('metadata', {})
            tags = metadata.get('tags', [])
            
            # Build metadata for indexing
            index_metadata = {
                'entities': entities,
                'tags': tags,
                'speakers': list(speakers),
                'language': result.get('language', 'en'),
                'created_at': metadata.get('created_at'),
                'confidence': metadata.get('confidence', 1.0),
                'duration': metadata.get('duration'),
                'word_count': len(content.split()),
                'segment_count': len(segments)
            }
            
            # Add any custom metadata
            for key, value in metadata.items():
                if key not in index_metadata:
                    index_metadata[key] = value
                    
            # Index the document
            await self.search_manager.index_transcript(
                transcript_id=doc_id,
                title=title,
                content=content,
                metadata=index_metadata
            )
            
            self.logger.info(f"Successfully indexed transcript: {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error indexing transcript: {e}")
            return False
            
    async def index_from_file(self, file_path: str) -> bool:
        """
        Index a transcript from a saved file
        
        Args:
            file_path: Path to transcript JSON file
            
        Returns:
            bool: Success status
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False
                
            # Load transcript data
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Use filename as title if not provided
            if 'title' not in data:
                data['title'] = path.stem
                
            # Use file path as ID if not provided
            if 'id' not in data:
                data['id'] = str(path.absolute())
                
            # Index the transcript
            return await self.index_transcription_result(data)
            
        except Exception as e:
            self.logger.error(f"Error indexing from file {file_path}: {e}")
            return False
            
    async def index_directory(self, directory_path: str, pattern: str = "*.json") -> Dict[str, bool]:
        """
        Index all transcript files in a directory
        
        Args:
            directory_path: Path to directory containing transcripts
            pattern: File pattern to match (default: *.json)
            
        Returns:
            Dict mapping file paths to success status
        """
        results = {}
        
        try:
            path = Path(directory_path)
            
            if not path.exists() or not path.is_dir():
                self.logger.error(f"Invalid directory: {directory_path}")
                return results
                
            # Find all matching files
            files = list(path.glob(pattern))
            
            self.logger.info(f"Found {len(files)} files to index in {directory_path}")
            
            # Index each file
            for file_path in files:
                success = await self.index_from_file(str(file_path))
                results[str(file_path)] = success
                
            # Log summary
            successful = sum(1 for success in results.values() if success)
            self.logger.info(
                f"Indexed {successful}/{len(files)} files successfully"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error indexing directory {directory_path}: {e}")
            return results
            
    async def update_transcript_metadata(self, 
                                       transcript_id: str,
                                       metadata_updates: Dict[str, Any]) -> bool:
        """
        Update metadata for an indexed transcript
        
        Args:
            transcript_id: ID of transcript to update
            metadata_updates: Metadata fields to update
            
        Returns:
            bool: Success status
        """
        try:
            # For now, we need to re-index with updated metadata
            # In a production system, you might want partial updates
            
            await self.search_manager.update_transcript(
                transcript_id,
                metadata_updates
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating transcript {transcript_id}: {e}")
            return False
            
    async def delete_transcript(self, transcript_id: str) -> bool:
        """
        Remove a transcript from the search index
        
        Args:
            transcript_id: ID of transcript to remove
            
        Returns:
            bool: Success status
        """
        try:
            await self.search_manager.delete_transcript(transcript_id)
            self.logger.info(f"Deleted transcript from index: {transcript_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting transcript {transcript_id}: {e}")
            return False
            
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Synchronous search wrapper for non-async contexts
        
        Args:
            query: Search query string
            **kwargs: Additional search options and filters
            
        Returns:
            Search results dictionary
        """
        # Create search query
        search_query = SearchQuery(
            query=query,
            filters=kwargs.get('filters', {}),
            options=kwargs.get('options', {})
        )
        
        # Run async search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.search_manager.search(search_query)
            )
            
            # Convert to dictionary for easy use
            return {
                'results': result.results,
                'total_count': result.total_count,
                'facets': result.facets,
                'search_time_ms': result.search_time_ms,
                'suggestions': result.suggestions,
                'has_results': result.has_results,
                'page_info': result.page_info
            }
            
        finally:
            loop.close()
            
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """
        Get search suggestions for autocomplete
        
        Args:
            partial_query: Partial search query
            
        Returns:
            List of suggested queries
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            suggestions = loop.run_until_complete(
                self.search_manager.get_search_suggestions(partial_query)
            )
            return suggestions
            
        finally:
            loop.close()
            
    def close(self):
        """Clean up resources"""
        self.search_manager.close()


# Convenience functions for easy integration

def create_search_integration(index_path: str = "search_index.db") -> SearchIntegration:
    """Create a search integration instance"""
    return SearchIntegration(index_path)


async def quick_index_transcript(transcript_data: Dict[str, Any], 
                               index_path: str = "search_index.db") -> bool:
    """Quick function to index a single transcript"""
    integration = SearchIntegration(index_path)
    try:
        return await integration.index_transcription_result(transcript_data)
    finally:
        integration.close()


def quick_search(query: str, 
                 index_path: str = "search_index.db",
                 **kwargs) -> Dict[str, Any]:
    """Quick function to perform a search"""
    integration = SearchIntegration(index_path)
    try:
        return integration.search(query, **kwargs)
    finally:
        integration.close()