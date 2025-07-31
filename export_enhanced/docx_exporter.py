"""
Microsoft Word (.docx) export functionality
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import tempfile
import os
from io import BytesIO

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.shared import OxmlElement, qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from database.models import Transcript, Annotation, User
from session_manager import TranscriptionResults


class DocxExportError(Exception):
    """Custom exception for DOCX export errors"""
    pass


class DocxExporter:
    """Export transcripts to Microsoft Word format with annotations"""
    
    def __init__(self):
        if not DOCX_AVAILABLE:
            raise DocxExportError(
                "python-docx library is not installed. "
                "Install with: pip install python-docx"
            )
    
    def export_transcript(
        self,
        transcript: Transcript,
        annotations: Optional[List[Annotation]] = None,
        include_metadata: bool = True,
        include_annotations: bool = True,
        include_entities: bool = True,
        custom_styles: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Export transcript to Word document
        
        Args:
            transcript: Transcript object to export
            annotations: List of annotations to include
            include_metadata: Whether to include document metadata
            include_annotations: Whether to include annotations as comments
            include_entities: Whether to include entity summary
            custom_styles: Custom styling options
            
        Returns:
            bytes: The generated Word document as bytes
        """
        # Create new document
        doc = Document()
        
        # Set up document properties
        if include_metadata:
            self._set_document_properties(doc, transcript)
        
        # Apply custom styles
        self._setup_styles(doc, custom_styles or {})
        
        # Add title
        title = doc.add_heading(transcript.title or 'Transcript', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add metadata section
        if include_metadata:
            self._add_metadata_section(doc, transcript)
        
        # Add transcript content
        self._add_transcript_content(doc, transcript, annotations if include_annotations else None)
        
        # Add entities section
        if include_entities and transcript.entities:
            self._add_entities_section(doc, transcript.entities)
        
        # Add annotations section (if not inline)
        if include_annotations and annotations and not include_annotations:
            self._add_annotations_section(doc, annotations)
        
        # Convert to bytes
        doc_bytes = BytesIO()
        doc.save(doc_bytes)
        doc_bytes.seek(0)
        
        return doc_bytes.getvalue()
    
    def export_results(
        self,
        results: TranscriptionResults,
        filename: Optional[str] = None,
        include_metadata: bool = True,
        include_entities: bool = True
    ) -> bytes:
        """
        Export TranscriptionResults to Word document
        
        Args:
            results: TranscriptionResults object to export
            filename: Optional filename for the document
            include_metadata: Whether to include metadata
            include_entities: Whether to include entities
            
        Returns:
            bytes: The generated Word document as bytes
        """
        # Create new document
        doc = Document()
        
        # Set up document properties
        if include_metadata:
            properties = doc.core_properties
            properties.title = filename or 'Transcript Export'
            properties.author = 'Audio/Video Transcription App'
            properties.created = datetime.utcnow()
            properties.modified = datetime.utcnow()
        
        # Apply default styles
        self._setup_styles(doc, {})
        
        # Add title
        title = doc.add_heading(filename or 'Transcript', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add metadata section
        if include_metadata:
            self._add_results_metadata_section(doc, results)
        
        # Add transcript content
        self._add_simple_transcript_content(doc, results.transcript)
        
        # Add entities section
        if include_entities and results.entities:
            self._add_entities_section(doc, results.entities)
        
        # Add summary section
        if results.summary:
            self._add_summary_section(doc, results.summary)
        
        # Convert to bytes
        doc_bytes = BytesIO()
        doc.save(doc_bytes)
        doc_bytes.seek(0)
        
        return doc_bytes.getvalue()
    
    def _set_document_properties(self, doc: Document, transcript: Transcript):
        """Set document metadata properties"""
        properties = doc.core_properties
        properties.title = transcript.title or 'Transcript'
        properties.author = f'User ID: {transcript.user_id}'
        properties.created = transcript.created_at
        properties.modified = transcript.updated_at
        properties.subject = 'Audio/Video Transcript'
        properties.keywords = 'transcript, audio, video, transcription'
        properties.comments = f'Generated by Audio/Video Transcription App'
    
    def _setup_styles(self, doc: Document, custom_styles: Dict[str, Any]):
        """Set up document styles"""
        styles = doc.styles
        
        # Modify Normal style
        normal_style = styles['Normal']
        normal_font = normal_style.font
        normal_font.name = custom_styles.get('font_name', 'Calibri')
        normal_font.size = Pt(custom_styles.get('font_size', 11))
        
        # Create custom styles
        try:
            # Metadata style
            metadata_style = styles.add_style('Metadata', WD_STYLE_TYPE.PARAGRAPH)
            metadata_font = metadata_style.font
            metadata_font.name = 'Calibri'
            metadata_font.size = Pt(9)
            metadata_font.italic = True
            metadata_style.paragraph_format.space_after = Pt(6)
        except:
            pass  # Style might already exist
        
        try:
            # Annotation style
            annotation_style = styles.add_style('Annotation', WD_STYLE_TYPE.PARAGRAPH)
            annotation_font = annotation_style.font
            annotation_font.name = 'Calibri'
            annotation_font.size = Pt(9)
            annotation_font.color.rgb = None  # Use theme color
            annotation_style.paragraph_format.left_indent = Inches(0.5)
            annotation_style.paragraph_format.space_before = Pt(3)
            annotation_style.paragraph_format.space_after = Pt(3)
        except:
            pass  # Style might already exist
    
    def _add_metadata_section(self, doc: Document, transcript: Transcript):
        """Add metadata information section"""
        doc.add_heading('Document Information', level=1)
        
        # Create table for metadata
        table = doc.add_table(rows=0, cols=2)
        table.style = 'Light Grid Accent 1'
        
        # Add metadata rows
        metadata_items = [
            ('File Name', transcript.file_name or 'N/A'),
            ('Created', transcript.created_at.strftime('%Y-%m-%d %H:%M:%S') if transcript.created_at else 'N/A'),
            ('Last Modified', transcript.updated_at.strftime('%Y-%m-%d %H:%M:%S') if transcript.updated_at else 'N/A'),
            ('Word Count', str(transcript.word_count or 0)),
            ('Language', transcript.language or 'Unknown'),
            ('Model Used', transcript.model_used or 'Unknown'),
            ('Confidence', f"{transcript.confidence:.2%}" if transcript.confidence else 'N/A'),
            ('Processing Time', f"{transcript.processing_time:.1f}s" if transcript.processing_time else 'N/A')
        ]
        
        for label, value in metadata_items:
            row = table.add_row()
            row.cells[0].text = label
            row.cells[1].text = value
            # Make label bold
            row.cells[0].paragraphs[0].runs[0].bold = True
        
        doc.add_paragraph()  # Add spacing
    
    def _add_results_metadata_section(self, doc: Document, results: TranscriptionResults):
        """Add metadata section for TranscriptionResults"""
        doc.add_heading('Document Information', level=1)
        
        # Create table for metadata
        table = doc.add_table(rows=0, cols=2)
        table.style = 'Light Grid Accent 1'
        
        # Add metadata rows
        metadata_items = [
            ('Export Date', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')),
            ('Word Count', str(results.word_count or 0)),
            ('Language', results.language or 'Unknown'),
            ('Model Used', results.model_used or 'Unknown'),
            ('Confidence', f"{results.confidence:.2%}" if results.confidence else 'N/A'),
            ('Processing Time', f"{results.processing_time:.1f}s" if results.processing_time else 'N/A')
        ]
        
        for label, value in metadata_items:
            row = table.add_row()
            row.cells[0].text = label
            row.cells[1].text = value
            # Make label bold
            row.cells[0].paragraphs[0].runs[0].bold = True
        
        doc.add_paragraph()  # Add spacing
    
    def _add_transcript_content(
        self, 
        doc: Document, 
        transcript: Transcript, 
        annotations: Optional[List[Annotation]] = None
    ):
        """Add the main transcript content with annotations"""
        doc.add_heading('Transcript', level=1)
        
        content = transcript.content or ''
        
        if annotations:
            # Add content with inline annotations
            self._add_annotated_content(doc, content, annotations)
        else:
            # Add simple content
            self._add_simple_transcript_content(doc, content)
    
    def _add_simple_transcript_content(self, doc: Document, content: str):
        """Add transcript content without annotations"""
        paragraphs = content.split('\n\n') if content else ['']
        
        for paragraph_text in paragraphs:
            if paragraph_text.strip():
                p = doc.add_paragraph()
                p.add_run(paragraph_text.strip())
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    def _add_annotated_content(
        self, 
        doc: Document, 
        content: str, 
        annotations: List[Annotation]
    ):
        """Add transcript content with inline annotations as comments"""
        # Group annotations by position
        position_annotations = {}
        for ann in annotations:
            if ann.position_start is not None:
                if ann.position_start not in position_annotations:
                    position_annotations[ann.position_start] = []
                position_annotations[ann.position_start].append(ann)
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n') if content else ['']
        current_position = 0
        
        for paragraph_text in paragraphs:
            if not paragraph_text.strip():
                continue
                
            p = doc.add_paragraph()
            paragraph_start = current_position
            paragraph_end = current_position + len(paragraph_text)
            
            # Check for annotations in this paragraph
            paragraph_annotations = []
            for pos in range(paragraph_start, paragraph_end + 1):
                if pos in position_annotations:
                    paragraph_annotations.extend(position_annotations[pos])
            
            if paragraph_annotations:
                # Add paragraph with annotation markers
                run = p.add_run(paragraph_text.strip())
                
                # Add footnote-style annotation references
                for i, ann in enumerate(paragraph_annotations, 1):
                    comment_run = p.add_run(f' [{i}]')
                    comment_run.font.superscript = True
                    comment_run.font.color.rgb = None  # Use theme color
            else:
                # Add simple paragraph
                p.add_run(paragraph_text.strip())
            
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            current_position = paragraph_end + 2  # Account for paragraph break
            
            # Add annotation details after paragraph if any
            if paragraph_annotations:
                for i, ann in enumerate(paragraph_annotations, 1):
                    ann_p = doc.add_paragraph(style='Annotation')
                    ann_run = ann_p.add_run(f'[{i}] ')
                    ann_run.bold = True
                    ann_p.add_run(f'{ann.user.username}: {ann.content}')
                    if ann.highlighted_text:
                        ann_p.add_run(f' (Re: "{ann.highlighted_text[:50]}...")')
    
    def _add_entities_section(self, doc: Document, entities: Dict[str, List[str]]):
        """Add entities summary section"""
        if not entities:
            return
            
        doc.add_heading('Extracted Entities', level=1)
        
        # Create table for entities
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Light Grid Accent 1'
        
        # Set headers
        header_row = table.rows[0]
        header_row.cells[0].text = 'Entity Type'
        header_row.cells[1].text = 'Entities'
        
        # Make headers bold
        for cell in header_row.cells:
            cell.paragraphs[0].runs[0].bold = True
        
        # Add entity data
        for entity_type, entity_list in entities.items():
            if entity_list:  # Only add if there are entities
                row = table.add_row()
                row.cells[0].text = entity_type.title()
                row.cells[1].text = ', '.join(entity_list)
        
        doc.add_paragraph()  # Add spacing
    
    def _add_summary_section(self, doc: Document, summary: str):
        """Add summary section"""
        if not summary:
            return
            
        doc.add_heading('Summary', level=1)
        p = doc.add_paragraph()
        p.add_run(summary)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        doc.add_paragraph()  # Add spacing
    
    def _add_annotations_section(self, doc: Document, annotations: List[Annotation]):
        """Add separate annotations section"""
        if not annotations:
            return
            
        doc.add_heading('Comments and Annotations', level=1)
        
        # Group annotations by parent (for threading)
        top_level_annotations = [ann for ann in annotations if not ann.parent_id]
        
        for i, ann in enumerate(top_level_annotations, 1):
            # Add annotation
            p = doc.add_paragraph()
            
            # Add annotation number and author
            num_run = p.add_run(f'{i}. ')
            num_run.bold = True
            
            author_run = p.add_run(f'{ann.user.username}')
            author_run.bold = True
            author_run.italic = True
            
            date_run = p.add_run(f' ({ann.created_at.strftime("%Y-%m-%d %H:%M")})')
            date_run.italic = True
            
            # Add highlighted text if any
            if ann.highlighted_text:
                p.add_run('\n')
                quote_run = p.add_run(f'Re: "{ann.highlighted_text}"')
                quote_run.italic = True
            
            # Add annotation content
            p.add_run(f'\n{ann.content}')
            
            # Add replies
            replies = [r for r in annotations if r.parent_id == ann.id]
            for reply in replies:
                reply_p = doc.add_paragraph()
                reply_p.paragraph_format.left_indent = Inches(0.5)
                
                reply_author = reply_p.add_run(f'↳ {reply.user.username}')
                reply_author.bold = True
                reply_author.italic = True
                
                reply_date = reply_p.add_run(f' ({reply.created_at.strftime("%Y-%m-%d %H:%M")})')
                reply_date.italic = True
                
                reply_p.add_run(f': {reply.content}')
            
            if i < len(top_level_annotations):
                doc.add_paragraph()  # Add spacing between annotations
    
    def create_temp_file(self, content: bytes, suffix: str = '.docx') -> str:
        """Create a temporary file with the document content"""
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=suffix,
            prefix='transcript_export_'
        )
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
    
    def cleanup_temp_file(self, filepath: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass  # Ignore cleanup errors