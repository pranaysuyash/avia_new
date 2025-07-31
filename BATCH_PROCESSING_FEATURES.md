# Batch Processing Features

## Overview

The Audio/Video Transcription App now includes comprehensive batch processing capabilities that leverage both standard processing and **OpenAI's native batch processing API** for maximum efficiency and cost savings. Users can process multiple files simultaneously with advanced queue management, progress tracking, and export functionality.

## Key Features

### 📦 Multiple File Upload
- **Simultaneous Processing**: Process 5-20 files at once for optimal performance
- **Mixed Format Support**: Handle MP3, WAV, MP4, and M4A files in the same batch
- **Smart Validation**: Automatic file size and format validation with clear feedback
- **Drag & Drop Interface**: Enhanced file upload experience with visual feedback

### 📊 Queue Management
- **Automatic Scheduling**: Intelligent job scheduling with configurable concurrency
- **Real-time Monitoring**: Live progress tracking for each file and overall batch
- **Error Handling**: Robust error recovery with detailed error reporting
- **Job Control**: Cancel, pause, or delete batch jobs as needed

### 🚀 Processing Pipeline
- **OpenAI Batch API Integration**: Automatic detection and use of OpenAI's batch processing for eligible jobs
- **50% Cost Savings**: Significant cost reduction when using OpenAI batch processing
- **Parallel Processing**: Multiple files processed simultaneously for efficiency
- **Smart Processing Selection**: Automatic fallback to standard processing when batch API isn't suitable
- **Progress Tracking**: Individual file progress and overall batch completion
- **Status Management**: Clear status indicators (Pending, Processing, Completed, Failed)
- **Resource Optimization**: Automatic resource management and cleanup

### 📥 Batch Export
- **Multiple Formats**: Export results in JSON, CSV, Excel, TXT, or ZIP formats
- **Comprehensive Reports**: Detailed processing statistics and summaries
- **Individual Transcripts**: Separate transcript files for each processed audio
- **Metadata Inclusion**: Optional job information and processing details

## User Interface

### Upload & Process Tab
- **File Selection**: Multi-file uploader with format validation
- **File Preview**: Table view of selected files with size and format information
- **Processing Configuration**: Job naming and analysis mode selection
- **Advanced Options**: Export settings and cleanup preferences

### Job Status Tab
- **Active Jobs**: Real-time monitoring of processing jobs
- **Progress Indicators**: Visual progress bars and completion percentages
- **Job Management**: Cancel, delete, or view details for each job
- **File Details**: Expandable view of individual file processing status

### Export Results Tab
- **Job Selection**: Choose from completed batch jobs
- **Format Options**: Select export format and metadata inclusion
- **Export Preview**: Preview of what will be exported
- **Download Management**: Direct download of exported results

## Technical Implementation

### Core Components

#### BatchProcessor
- **Queue Management**: Thread-safe job queue with configurable concurrency
- **OpenAI Batch Integration**: Automatic detection and submission of eligible jobs to OpenAI batch API
- **Hybrid Processing**: Seamless switching between batch and standard processing methods
- **Worker Threads**: Background processing with automatic error handling
- **Progress Callbacks**: Real-time progress updates to the UI
- **Resource Cleanup**: Automatic temporary file management

#### OpenAIBatchProcessor
- **Batch Job Creation**: Automatic JSONL file generation for OpenAI batch API
- **Status Monitoring**: Real-time tracking of OpenAI batch job progress
- **Result Processing**: Automatic parsing and integration of batch results
- **Cost Optimization**: 50% cost reduction through batch API usage
- **Error Handling**: Graceful fallback to standard processing on batch failures

#### BatchExporter
- **Format Support**: JSON, CSV, Excel, TXT, and ZIP export formats
- **Data Transformation**: Convert processing results to various output formats
- **Metadata Handling**: Include job information and processing statistics
- **File Management**: Generate appropriate filenames and handle large exports

#### BatchInterface
- **Streamlit Integration**: Native Streamlit components for batch processing
- **State Management**: Persistent job state across sessions
- **User Experience**: Intuitive interface with helpful tips and guidance
- **Error Display**: Clear error messages and recovery suggestions

### Data Models

#### BatchJob
```python
@dataclass
class BatchJob:
    id: str
    name: str
    files: List[BatchFile]
    analysis_mode: str
    status: BatchJobStatus
    total_files: int
    completed_files: int
    failed_files: int
    results: Dict[str, BatchResults]
```

#### BatchFile
```python
@dataclass
class BatchFile:
    id: str
    name: str
    size_bytes: int
    format: str
    temp_path: str
    status: BatchJobStatus
    progress: int
    processing_time: float
```

#### BatchResults
```python
@dataclass
class BatchResults:
    file_id: str
    transcript: str
    entities: Dict[str, Any]
    summary: str
    confidence: float
    word_count: int
```

## Usage Examples

### Basic Batch Processing
1. **Upload Files**: Select multiple audio/video files using the file uploader
2. **Configure Job**: Set job name and choose analysis mode
3. **Start Processing**: Click "Start Batch Processing" to begin
4. **Monitor Progress**: Switch to Job Status tab to track progress
5. **Export Results**: Use Export Results tab when processing completes

### Advanced Configuration
```python
# Processing Options
{
    "auto_export": True,
    "export_format": "zip",
    "include_metadata": True,
    "cleanup_after_export": False
}
```

### Export Formats

#### JSON Export
- **Structure**: Hierarchical JSON with job info and results
- **Content**: Full transcripts, entities, and metadata
- **Use Case**: API integration and data analysis

#### CSV Export
- **Format**: Flat table structure with all data
- **Content**: One row per file with all processing results
- **Use Case**: Spreadsheet analysis and reporting

#### Excel Export
- **Sheets**: Multiple worksheets (Summary, Results, Transcripts, Entities)
- **Content**: Organized data with formatting and charts
- **Use Case**: Business reporting and presentation

#### ZIP Export
- **Contents**: All formats bundled together
- **Structure**: Organized folder structure with individual files
- **Use Case**: Complete data package for archival

## Performance Considerations

### Optimal Batch Sizes
- **Small Files (< 5MB)**: 15-20 files per batch
- **Medium Files (5-25MB)**: 8-12 files per batch
- **Large Files (25-100MB)**: 3-5 files per batch

### Processing Time Estimates
- **Basic Mode**: ~2 seconds per MB of audio
- **Advanced Mode**: ~5 seconds per MB of audio
- **Advanced+ Mode**: ~8 seconds per MB of audio

### Resource Usage
- **Memory**: ~100MB per concurrent file
- **Storage**: Temporary files require 2x original file size
- **Network**: API calls for Advanced modes require stable connection

## Error Handling

### File-Level Errors
- **Invalid Format**: Clear error message with supported formats
- **File Too Large**: Size limit warning with compression suggestions
- **Corrupted File**: Detailed error with file validation results
- **Processing Failure**: Specific error message with retry options

### Job-Level Errors
- **API Failures**: Automatic retry with exponential backoff
- **Network Issues**: Graceful degradation to local processing
- **Resource Limits**: Queue management with priority handling
- **System Errors**: Comprehensive logging and error reporting

## Best Practices

### File Preparation
- **Consistent Quality**: Use similar audio quality across files
- **Optimal Size**: Keep files under 100MB when possible
- **Clear Audio**: Ensure minimal background noise
- **Proper Naming**: Use descriptive filenames for easy identification

### Batch Configuration
- **Appropriate Mode**: Choose analysis mode based on requirements
- **Reasonable Size**: Don't exceed recommended batch sizes
- **Network Stability**: Ensure stable connection for Advanced modes
- **Storage Space**: Verify sufficient disk space for processing

### Export Management
- **Format Selection**: Choose appropriate format for intended use
- **Metadata Inclusion**: Include metadata for audit trails
- **File Organization**: Use descriptive job names for easy identification
- **Regular Cleanup**: Remove old jobs to free up storage

## Integration with Existing Features

### Session Management
- **State Persistence**: Batch jobs persist across browser sessions
- **History Tracking**: Processing history includes batch operations
- **Preference Storage**: User preferences apply to batch processing

### Analysis Modes
- **Basic Mode**: Fast local processing with spaCy NER
- **Advanced Mode**: AI-powered analysis with OpenAI GPT
- **Advanced+ Mode**: Full feature set with speaker diarization

### Export Compatibility
- **Single File Results**: Batch exports compatible with single-file processing
- **Format Consistency**: Same export formats available for both modes
- **Data Structure**: Consistent data models across processing types

## Future Enhancements

### Planned Features
- **Scheduled Processing**: Queue jobs for future processing
- **Priority Queues**: High-priority job processing
- **Distributed Processing**: Multi-server batch processing
- **Advanced Analytics**: Batch-level insights and reporting

### API Integration
- **REST API**: Programmatic batch job submission
- **Webhooks**: Real-time progress notifications
- **Bulk Operations**: API endpoints for bulk job management
- **Status Monitoring**: External monitoring and alerting

## Troubleshooting

### Common Issues

#### "Batch processing not starting"
- **Check**: Ensure files are valid and within size limits
- **Solution**: Verify file formats and reduce batch size if needed

#### "Jobs stuck in processing"
- **Check**: Network connection and API key configuration
- **Solution**: Cancel and restart job, check system resources

#### "Export fails with large batches"
- **Check**: Available disk space and memory
- **Solution**: Export in smaller chunks or use ZIP format

#### "Progress not updating"
- **Check**: Browser refresh and network connectivity
- **Solution**: Refresh page or check job status manually

### Support Resources
- **Logs**: Check application logs for detailed error information
- **Documentation**: Refer to this guide for configuration help
- **Testing**: Use test files to verify system functionality
- **Community**: Report issues and get help from the community

## Conclusion

The batch processing feature significantly enhances the Audio/Video Transcription App's capabilities, enabling efficient processing of multiple files with comprehensive monitoring and export options. The implementation follows best practices for scalability, reliability, and user experience while maintaining compatibility with existing features.

For technical support or feature requests, please refer to the project documentation or submit an issue through the appropriate channels.