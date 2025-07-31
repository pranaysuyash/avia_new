#!/usr/bin/env python3
"""
Batch Export Module for Audio/Video Transcription App
Handles exporting batch processing results in various formats
"""

import os
import logging
import json
import csv
import zipfile
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from io import StringIO, BytesIO

from batch_processor import BatchJob, BatchResults, BatchFile

logger = logging.getLogger(__name__)

class BatchExporter:
    """Handles exporting batch processing results in multiple formats"""
    
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'xlsx', 'txt', 'zip']
    
    def export_job_results(self, job: BatchJob, format_type: str, include_metadata: bool = True) -> bytes:
        """Export job results in specified format"""
        
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}. Supported: {self.supported_formats}")
        
        try:
            if format_type == 'json':
                return self._export_json(job, include_metadata)
            elif format_type == 'csv':
                return self._export_csv(job, include_metadata)
            elif format_type == 'xlsx':
                return self._export_xlsx(job, include_metadata)
            elif format_type == 'txt':
                return self._export_txt(job, include_metadata)
            elif format_type == 'zip':
                return self._export_zip(job, include_metadata)
            
        except Exception as e:
            logger.error(f"Failed to export job {job.id} as {format_type}: {e}")
            raise
    
    def _export_json(self, job: BatchJob, include_metadata: bool) -> bytes:
        """Export results as JSON"""
        
        export_data = {
            'job_info': {
                'id': job.id,
                'name': job.name,
                'analysis_mode': job.analysis_mode,
                'created_time': job.created_time.isoformat() if job.created_time else None,
                'start_time': job.start_time.isoformat() if job.start_time else None,
                'end_time': job.end_time.isoformat() if job.end_time else None,
                'total_files': job.total_files,
                'completed_files': job.completed_files,
                'failed_files': job.failed_files,
                'summary': job.get_summary()
            },
            'results': []
        }
        
        # Add results for each file
        for file_obj in job.files:
            file_data = {
                'file_info': {
                    'id': file_obj.id,
                    'name': file_obj.name,
                    'size_bytes': file_obj.size_bytes,
                    'format': file_obj.format,
                    'status': file_obj.status.value,
                    'processing_time': file_obj.processing_time
                }
            }
            
            # Add processing results if available
            if file_obj.id in job.results:
                result = job.results[file_obj.id]
                file_data['transcription'] = {
                    'transcript': result.transcript,
                    'word_count': result.word_count,
                    'confidence': result.confidence,
                    'language': result.language,
                    'model_used': result.model_used
                }
                file_data['entities'] = result.entities
                if result.summary:
                    file_data['summary'] = result.summary
            
            # Add error info if failed
            if file_obj.status.value == 'failed':
                file_data['error'] = file_obj.error_message
            
            export_data['results'].append(file_data)
        
        # Add metadata if requested
        if include_metadata:
            export_data['export_metadata'] = {
                'export_time': datetime.now().isoformat(),
                'export_format': 'json',
                'exporter_version': '1.0'
            }
        
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        return json_str.encode('utf-8')
    
    def _export_csv(self, job: BatchJob, include_metadata: bool) -> bytes:
        """Export results as CSV"""
        
        output = StringIO()
        
        # Write metadata header if requested
        if include_metadata:
            writer = csv.writer(output)
            writer.writerow(['# Batch Processing Results Export'])
            writer.writerow(['# Job ID:', job.id])
            writer.writerow(['# Job Name:', job.name])
            writer.writerow(['# Analysis Mode:', job.analysis_mode])
            writer.writerow(['# Export Time:', datetime.now().isoformat()])
            writer.writerow(['# Total Files:', job.total_files])
            writer.writerow(['# Completed Files:', job.completed_files])
            writer.writerow(['# Failed Files:', job.failed_files])
            writer.writerow([])  # Empty row
        
        # Define CSV columns
        fieldnames = [
            'file_id', 'file_name', 'file_size_bytes', 'file_format', 'status',
            'processing_time', 'transcript', 'word_count', 'confidence', 'language',
            'model_used', 'summary', 'entities_json', 'error_message'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write data for each file
        for file_obj in job.files:
            row_data = {
                'file_id': file_obj.id,
                'file_name': file_obj.name,
                'file_size_bytes': file_obj.size_bytes,
                'file_format': file_obj.format,
                'status': file_obj.status.value,
                'processing_time': file_obj.processing_time,
                'transcript': '',
                'word_count': 0,
                'confidence': 0.0,
                'language': '',
                'model_used': '',
                'summary': '',
                'entities_json': '',
                'error_message': file_obj.error_message if file_obj.status.value == 'failed' else ''
            }
            
            # Add results if available
            if file_obj.id in job.results:
                result = job.results[file_obj.id]
                row_data.update({
                    'transcript': result.transcript,
                    'word_count': result.word_count,
                    'confidence': result.confidence,
                    'language': result.language,
                    'model_used': result.model_used,
                    'summary': result.summary,
                    'entities_json': json.dumps(result.entities) if result.entities else ''
                })
            
            writer.writerow(row_data)
        
        return output.getvalue().encode('utf-8')
    
    def _export_xlsx(self, job: BatchJob, include_metadata: bool) -> bytes:
        """Export results as Excel file"""
        
        output = BytesIO()
        
        # Create Excel writer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Create summary sheet
            if include_metadata:
                summary_data = {
                    'Property': [
                        'Job ID', 'Job Name', 'Analysis Mode', 'Export Time',
                        'Total Files', 'Completed Files', 'Failed Files',
                        'Total Words', 'Average Confidence', 'Processing Time (seconds)'
                    ],
                    'Value': [
                        job.id, job.name, job.analysis_mode, datetime.now().isoformat(),
                        job.total_files, job.completed_files, job.failed_files,
                        job.get_summary()['total_words'],
                        f"{job.get_summary()['average_confidence']:.3f}",
                        f"{job.get_summary()['processing_time']:.2f}"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create main results sheet
            results_data = []
            for file_obj in job.files:
                row_data = {
                    'File ID': file_obj.id,
                    'File Name': file_obj.name,
                    'File Size (bytes)': file_obj.size_bytes,
                    'File Format': file_obj.format,
                    'Status': file_obj.status.value,
                    'Processing Time (s)': file_obj.processing_time,
                    'Word Count': 0,
                    'Confidence': 0.0,
                    'Language': '',
                    'Model Used': '',
                    'Error Message': file_obj.error_message if file_obj.status.value == 'failed' else ''
                }
                
                # Add results if available
                if file_obj.id in job.results:
                    result = job.results[file_obj.id]
                    row_data.update({
                        'Word Count': result.word_count,
                        'Confidence': result.confidence,
                        'Language': result.language,
                        'Model Used': result.model_used
                    })
                
                results_data.append(row_data)
            
            results_df = pd.DataFrame(results_data)
            results_df.to_excel(writer, sheet_name='Results', index=False)
            
            # Create transcripts sheet
            transcript_data = []
            for file_obj in job.files:
                if file_obj.id in job.results:
                    result = job.results[file_obj.id]
                    transcript_data.append({
                        'File Name': file_obj.name,
                        'Transcript': result.transcript,
                        'Summary': result.summary
                    })
            
            if transcript_data:
                transcript_df = pd.DataFrame(transcript_data)
                transcript_df.to_excel(writer, sheet_name='Transcripts', index=False)
            
            # Create entities sheet
            entity_data = []
            for file_obj in job.files:
                if file_obj.id in job.results:
                    result = job.results[file_obj.id]
                    if result.entities:
                        for entity_type, entities in result.entities.items():
                            for entity in entities:
                                entity_data.append({
                                    'File Name': file_obj.name,
                                    'Entity Type': entity_type,
                                    'Entity': entity
                                })
            
            if entity_data:
                entity_df = pd.DataFrame(entity_data)
                entity_df.to_excel(writer, sheet_name='Entities', index=False)
        
        return output.getvalue()
    
    def _export_txt(self, job: BatchJob, include_metadata: bool) -> bytes:
        """Export results as plain text"""
        
        output = StringIO()
        
        # Write header
        if include_metadata:
            output.write("=" * 60 + "\n")
            output.write("BATCH PROCESSING RESULTS\n")
            output.write("=" * 60 + "\n\n")
            output.write(f"Job ID: {job.id}\n")
            output.write(f"Job Name: {job.name}\n")
            output.write(f"Analysis Mode: {job.analysis_mode}\n")
            output.write(f"Export Time: {datetime.now().isoformat()}\n")
            output.write(f"Total Files: {job.total_files}\n")
            output.write(f"Completed Files: {job.completed_files}\n")
            output.write(f"Failed Files: {job.failed_files}\n\n")
        
        # Write results for each file
        for i, file_obj in enumerate(job.files, 1):
            output.write(f"FILE {i}: {file_obj.name}\n")
            output.write("-" * 40 + "\n")
            output.write(f"Status: {file_obj.status.value}\n")
            output.write(f"Size: {file_obj.size_bytes} bytes\n")
            output.write(f"Format: {file_obj.format}\n")
            output.write(f"Processing Time: {file_obj.processing_time:.2f}s\n")
            
            if file_obj.status.value == 'failed':
                output.write(f"Error: {file_obj.error_message}\n")
            elif file_obj.id in job.results:
                result = job.results[file_obj.id]
                output.write(f"Word Count: {result.word_count}\n")
                output.write(f"Confidence: {result.confidence:.3f}\n")
                output.write(f"Language: {result.language}\n")
                output.write(f"Model: {result.model_used}\n\n")
                
                if result.summary:
                    output.write("SUMMARY:\n")
                    output.write(result.summary + "\n\n")
                
                output.write("TRANSCRIPT:\n")
                output.write(result.transcript + "\n\n")
                
                if result.entities:
                    output.write("ENTITIES:\n")
                    for entity_type, entities in result.entities.items():
                        if entities:
                            output.write(f"  {entity_type}: {', '.join(entities)}\n")
                    output.write("\n")
            
            output.write("\n" + "=" * 60 + "\n\n")
        
        return output.getvalue().encode('utf-8')
    
    def _export_zip(self, job: BatchJob, include_metadata: bool) -> bytes:
        """Export results as ZIP file containing multiple formats"""
        
        output = BytesIO()
        
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # Add JSON export
            json_data = self._export_json(job, include_metadata)
            zipf.writestr(f"{job.name}_results.json", json_data)
            
            # Add CSV export
            csv_data = self._export_csv(job, include_metadata)
            zipf.writestr(f"{job.name}_results.csv", csv_data)
            
            # Add text export
            txt_data = self._export_txt(job, include_metadata)
            zipf.writestr(f"{job.name}_results.txt", txt_data)
            
            # Add Excel export
            try:
                xlsx_data = self._export_xlsx(job, include_metadata)
                zipf.writestr(f"{job.name}_results.xlsx", xlsx_data)
            except Exception as e:
                logger.warning(f"Failed to add Excel file to ZIP: {e}")
            
            # Add individual transcript files
            for file_obj in job.files:
                if file_obj.id in job.results:
                    result = job.results[file_obj.id]
                    if result.transcript:
                        filename = f"transcripts/{file_obj.name}_transcript.txt"
                        zipf.writestr(filename, result.transcript.encode('utf-8'))
        
        return output.getvalue()
    
    def get_export_filename(self, job: BatchJob, format_type: str) -> str:
        """Generate appropriate filename for export"""
        
        # Clean job name for filename
        clean_name = "".join(c for c in job.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_name = clean_name.replace(' ', '_')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{clean_name}_{timestamp}.{format_type}"
    
    def get_export_stats(self, job: BatchJob) -> Dict[str, Any]:
        """Get statistics about what will be exported"""
        
        stats = {
            'total_files': job.total_files,
            'completed_files': job.completed_files,
            'failed_files': job.failed_files,
            'total_transcripts': len([f for f in job.files if f.id in job.results and job.results[f.id].transcript]),
            'total_words': sum(result.word_count for result in job.results.values()),
            'total_entities': sum(
                sum(len(entities) for entities in result.entities.values()) 
                for result in job.results.values() 
                if result.entities
            ),
            'has_summaries': any(result.summary for result in job.results.values()),
            'supported_formats': self.supported_formats
        }
        
        return stats

# Global batch exporter instance
batch_exporter = BatchExporter()