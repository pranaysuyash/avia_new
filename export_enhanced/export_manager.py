"""
Enhanced export manager for coordinating different export formats
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import json
from io import BytesIO

from database.models import Transcript, Annotation, User
from session_manager import TranscriptionResults
from .docx_exporter import DocxExporter, DocxExportError


class ExportManager:
    """Manages various export formats and options"""
    
    def __init__(self):
        self.docx_exporter = None
        self._init_docx_exporter()
    
    def _init_docx_exporter(self):
        """Initialize DOCX exporter if available"""
        try:
            self.docx_exporter = DocxExporter()
        except DocxExportError:
            self.docx_exporter = None
    
    def export_transcript(
        self,
        transcript: Transcript,
        format_type: str,
        annotations: Optional[List[Annotation]] = None,
        export_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export transcript in specified format
        
        Args:
            transcript: Transcript to export
            format_type: Export format ('text', 'json', 'markdown', 'docx')
            annotations: Optional annotations to include
            export_options: Format-specific options
            
        Returns:
            Dict with 'content' (bytes/str), 'filename', 'mime_type'
        """
        options = export_options or {}
        
        if format_type.lower() == 'text':
            return self._export_text(transcript, annotations, options)
        elif format_type.lower() == 'json':
            return self._export_json(transcript, annotations, options)
        elif format_type.lower() == 'markdown':
            return self._export_markdown(transcript, annotations, options)
        elif format_type.lower() == 'docx':
            return self._export_docx(transcript, annotations, options)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def export_results(
        self,
        results: TranscriptionResults,
        format_type: str,
        filename: Optional[str] = None,
        export_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export TranscriptionResults in specified format
        
        Args:
            results: TranscriptionResults to export
            format_type: Export format ('text', 'json', 'markdown', 'docx')
            filename: Base filename for export
            export_options: Format-specific options
            
        Returns:
            Dict with 'content' (bytes/str), 'filename', 'mime_type'
        """
        options = export_options or {}
        base_filename = filename or 'transcript'
        
        if format_type.lower() == 'text':
            return self._export_results_text(results, base_filename, options)
        elif format_type.lower() == 'json':
            return self._export_results_json(results, base_filename, options)
        elif format_type.lower() == 'markdown':
            return self._export_results_markdown(results, base_filename, options)
        elif format_type.lower() == 'docx':
            return self._export_results_docx(results, base_filename, options)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_text(
        self,
        transcript: Transcript,
        annotations: Optional[List[Annotation]],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export as plain text"""
        content = f"Transcript: {transcript.title or 'Untitled'}\n"
        content += "=" * 50 + "\n\n"
        content += transcript.content or ""
        
        # Add metadata if requested
        if options.get('include_metadata', True):
            content += "\n\n" + "=" * 50 + "\n"
            content += "METADATA\n"
            content += "=" * 50 + "\n"
            content += f"Created: {transcript.created_at}\n" if transcript.created_at else ""
            content += f"File: {transcript.file_name}\n" if transcript.file_name else ""
            content += f"Words: {transcript.word_count}\n" if transcript.word_count else ""
            content += f"Language: {transcript.language}\n" if transcript.language else ""
            content += f"Model: {transcript.model_used}\n" if transcript.model_used else ""
            content += f"Confidence: {transcript.confidence:.2%}\n" if transcript.confidence else ""
        
        # Add entities if available
        if options.get('include_entities', True) and transcript.entities:
            content += "\n\n" + "=" * 50 + "\n"
            content += "ENTITIES\n"
            content += "=" * 50 + "\n"
            entities = transcript.entities
            if isinstance(entities, str):
                entities = json.loads(entities)
            for entity_type, entity_list in entities.items():
                if entity_list:
                    content += f"{entity_type.title()}: {', '.join(entity_list)}\n"
        
        # Add annotations if requested
        if options.get('include_annotations', True) and annotations:
            content += "\n\n" + "=" * 50 + "\n"
            content += "COMMENTS & ANNOTATIONS\n"
            content += "=" * 50 + "\n"
            
            top_level_annotations = [ann for ann in annotations if not ann.parent_id]
            for i, ann in enumerate(top_level_annotations, 1):
                content += f"\n{i}. {ann.user.username} ({ann.created_at.strftime('%Y-%m-%d %H:%M')})\n"
                if ann.highlighted_text:
                    content += f"   Re: \"{ann.highlighted_text}\"\n"
                content += f"   {ann.content}\n"
                
                # Add replies
                replies = [r for r in annotations if r.parent_id == ann.id]
                for reply in replies:
                    content += f"   → {reply.user.username}: {reply.content}\n"
        
        return {
            'content': content,
            'filename': f"{transcript.title or 'transcript'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            'mime_type': 'text/plain'
        }
    
    def _export_json(
        self,
        transcript: Transcript,
        annotations: Optional[List[Annotation]],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export as JSON"""
        data = {
            'transcript': {
                'id': transcript.id,
                'title': transcript.title,
                'content': transcript.content,
                'created_at': transcript.created_at.isoformat() if transcript.created_at else None,
                'updated_at': transcript.updated_at.isoformat() if transcript.updated_at else None,
                'metadata': {
                    'file_name': transcript.file_name,
                    'file_size': transcript.file_size,
                    'word_count': transcript.word_count,
                    'language': transcript.language,
                    'confidence': transcript.confidence,
                    'model_used': transcript.model_used,
                    'processing_time': transcript.processing_time
                }
            }
        }
        
        # Add entities if available
        if options.get('include_entities', True) and transcript.entities:
            entities = transcript.entities
            if isinstance(entities, str):
                entities = json.loads(entities)
            data['entities'] = entities
        
        # Add summary if available
        if transcript.summary:
            data['summary'] = transcript.summary
        
        # Add annotations if requested
        if options.get('include_annotations', True) and annotations:
            data['annotations'] = []
            for ann in annotations:
                ann_data = {
                    'id': ann.id,
                    'user': ann.user.username,
                    'content': ann.content,
                    'highlighted_text': ann.highlighted_text,
                    'position_start': ann.position_start,
                    'position_end': ann.position_end,
                    'parent_id': ann.parent_id,
                    'is_resolved': ann.is_resolved,
                    'created_at': ann.created_at.isoformat() if ann.created_at else None,
                    'updated_at': ann.updated_at.isoformat() if ann.updated_at else None
                }
                data['annotations'].append(ann_data)
        
        content = json.dumps(data, indent=2)
        
        return {
            'content': content,
            'filename': f"{transcript.title or 'transcript'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            'mime_type': 'application/json'
        }
    
    def _export_markdown(
        self,
        transcript: Transcript,
        annotations: Optional[List[Annotation]],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export as Markdown"""
        content = f"# {transcript.title or 'Transcript'}\n\n"
        
        # Add metadata if requested
        if options.get('include_metadata', True):
            content += "## Document Information\n\n"
            content += "| Field | Value |\n"
            content += "|-------|-------|\n"
            if transcript.created_at:
                content += f"| Created | {transcript.created_at.strftime('%Y-%m-%d %H:%M:%S')} |\n"
            if transcript.file_name:
                content += f"| File Name | {transcript.file_name} |\n"
            if transcript.word_count:
                content += f"| Word Count | {transcript.word_count} |\n"
            if transcript.language:
                content += f"| Language | {transcript.language} |\n"
            if transcript.model_used:
                content += f"| Model | {transcript.model_used} |\n"
            if transcript.confidence:
                content += f"| Confidence | {transcript.confidence:.2%} |\n"
            content += "\n"
        
        # Add transcript content
        content += "## Transcript\n\n"
        transcript_text = transcript.content or ""
        
        # Format transcript content
        paragraphs = transcript_text.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                content += f"{paragraph.strip()}\n\n"
        
        # Add entities if available
        if options.get('include_entities', True) and transcript.entities:
            content += "## Extracted Entities\n\n"
            entities = transcript.entities
            if isinstance(entities, str):
                entities = json.loads(entities)
            for entity_type, entity_list in entities.items():
                if entity_list:
                    content += f"**{entity_type.title()}**: {', '.join(entity_list)}\n\n"
        
        # Add summary if available
        if transcript.summary:
            content += "## Summary\n\n"
            content += f"{transcript.summary}\n\n"
        
        # Add annotations if requested
        if options.get('include_annotations', True) and annotations:
            content += "## Comments & Annotations\n\n"
            
            top_level_annotations = [ann for ann in annotations if not ann.parent_id]
            for i, ann in enumerate(top_level_annotations, 1):
                content += f"### {i}. {ann.user.username}\n"
                content += f"*{ann.created_at.strftime('%Y-%m-%d %H:%M')}*\n\n"
                
                if ann.highlighted_text:
                    content += f"> {ann.highlighted_text}\n\n"
                
                content += f"{ann.content}\n\n"
                
                # Add replies
                replies = [r for r in annotations if r.parent_id == ann.id]
                if replies:
                    content += "**Replies:**\n\n"
                    for reply in replies:
                        content += f"- **{reply.user.username}** _{reply.created_at.strftime('%Y-%m-%d %H:%M')}_: {reply.content}\n"
                    content += "\n"
                
                content += "---\n\n"
        
        return {
            'content': content,
            'filename': f"{transcript.title or 'transcript'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            'mime_type': 'text/markdown'
        }
    
    def _export_docx(
        self,
        transcript: Transcript,
        annotations: Optional[List[Annotation]],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export as Word document"""
        if not self.docx_exporter:
            raise DocxExportError("DOCX exporter not available. Install python-docx.")
        
        content_bytes = self.docx_exporter.export_transcript(
            transcript=transcript,
            annotations=annotations,
            include_metadata=options.get('include_metadata', True),
            include_annotations=options.get('include_annotations', True),
            include_entities=options.get('include_entities', True),
            custom_styles=options.get('custom_styles')
        )
        
        return {
            'content': content_bytes,
            'filename': f"{transcript.title or 'transcript'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
    
    def _export_results_text(
        self,
        results: TranscriptionResults,
        base_filename: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export TranscriptionResults as text"""
        content = f"Transcript\n"
        content += "=" * 50 + "\n\n"
        content += results.transcript or ""
        
        # Add metadata if requested
        if options.get('include_metadata', True):
            content += "\n\n" + "=" * 50 + "\n"
            content += "METADATA\n"
            content += "=" * 50 + "\n"
            content += f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += f"Words: {results.word_count}\n" if results.word_count else ""
            content += f"Language: {results.language}\n" if results.language else ""
            content += f"Model: {results.model_used}\n" if results.model_used else ""
            content += f"Confidence: {results.confidence:.2%}\n" if results.confidence else ""
            content += f"Processing Time: {results.processing_time:.1f}s\n" if results.processing_time else ""
        
        # Add entities if available
        if options.get('include_entities', True) and results.entities:
            content += "\n\n" + "=" * 50 + "\n"
            content += "ENTITIES\n"
            content += "=" * 50 + "\n"
            for entity_type, entity_list in results.entities.items():
                if entity_list:
                    content += f"{entity_type.title()}: {', '.join(entity_list)}\n"
        
        # Add summary if available
        if results.summary:
            content += "\n\n" + "=" * 50 + "\n"
            content += "SUMMARY\n"
            content += "=" * 50 + "\n"
            content += results.summary + "\n"
        
        return {
            'content': content,
            'filename': f"{base_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            'mime_type': 'text/plain'
        }
    
    def _export_results_json(
        self,
        results: TranscriptionResults,
        base_filename: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export TranscriptionResults as JSON"""
        data = {
            'transcript': results.transcript,
            'entities': results.entities,
            'summary': results.summary,
            'metadata': {
                'word_count': results.word_count,
                'confidence': results.confidence,
                'processing_time': results.processing_time,
                'model_used': results.model_used,
                'language': results.language,
                'export_date': datetime.now().isoformat()
            }
        }
        
        content = json.dumps(data, indent=2)
        
        return {
            'content': content,
            'filename': f"{base_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            'mime_type': 'application/json'
        }
    
    def _export_results_markdown(
        self,
        results: TranscriptionResults,
        base_filename: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export TranscriptionResults as Markdown"""
        content = f"# {base_filename.title()}\n\n"
        
        # Add metadata if requested
        if options.get('include_metadata', True):
            content += "## Document Information\n\n"
            content += "| Field | Value |\n"
            content += "|-------|-------|\n"
            content += f"| Export Date | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |\n"
            if results.word_count:
                content += f"| Word Count | {results.word_count} |\n"
            if results.language:
                content += f"| Language | {results.language} |\n"
            if results.model_used:
                content += f"| Model | {results.model_used} |\n"
            if results.confidence:
                content += f"| Confidence | {results.confidence:.2%} |\n"
            if results.processing_time:
                content += f"| Processing Time | {results.processing_time:.1f}s |\n"
            content += "\n"
        
        # Add transcript content
        content += "## Transcript\n\n"
        transcript_text = results.transcript or ""
        
        # Format transcript content
        paragraphs = transcript_text.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                content += f"{paragraph.strip()}\n\n"
        
        # Add entities if available
        if options.get('include_entities', True) and results.entities:
            content += "## Extracted Entities\n\n"
            for entity_type, entity_list in results.entities.items():
                if entity_list:
                    content += f"**{entity_type.title()}**: {', '.join(entity_list)}\n\n"
        
        # Add summary if available
        if results.summary:
            content += "## Summary\n\n"
            content += f"{results.summary}\n\n"
        
        return {
            'content': content,
            'filename': f"{base_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            'mime_type': 'text/markdown'
        }
    
    def _export_results_docx(
        self,
        results: TranscriptionResults,
        base_filename: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export TranscriptionResults as Word document"""
        if not self.docx_exporter:
            raise DocxExportError("DOCX exporter not available. Install python-docx.")
        
        content_bytes = self.docx_exporter.export_results(
            results=results,
            filename=base_filename,
            include_metadata=options.get('include_metadata', True),
            include_entities=options.get('include_entities', True)
        )
        
        return {
            'content': content_bytes,
            'filename': f"{base_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
    
    def get_available_formats(self) -> List[str]:
        """Get list of available export formats"""
        formats = ['text', 'json', 'markdown']
        if self.docx_exporter:
            formats.append('docx')
        return formats
    
    def is_format_available(self, format_type: str) -> bool:
        """Check if a specific format is available"""
        return format_type.lower() in self.get_available_formats()