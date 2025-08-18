"""Log aggregation and centralized collection system."""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: str
    level: str
    service: str
    component: str
    correlation_id: str
    message: str
    extra_data: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LogQuery:
    """Query parameters for log search."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    services: Optional[List[str]] = None
    levels: Optional[List[str]] = None
    correlation_id: Optional[str] = None
    message_contains: Optional[str] = None
    limit: int = 1000


class LogAggregator:
    """Aggregates logs from multiple sources."""
    
    def __init__(self, log_dir: Path, buffer_size: int = 10000):
        self.log_dir = Path(log_dir)
        self.buffer_size = buffer_size
        self.log_buffer: List[LogEntry] = []
        self.aggregated_file = self.log_dir / "aggregated.jsonl"
        self._ensure_log_directory()
        
    def _ensure_log_directory(self):
        """Ensure log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    async def collect_logs(self, sources: List[Path]) -> None:
        """Collect logs from multiple sources."""
        for source in sources:
            if source.exists() and source.is_file():
                await self._process_log_file(source)
            else:
                logger.warning(f"Log source not found: {source}")
                
    async def _process_log_file(self, log_file: Path) -> None:
        """Process a single log file."""
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        log_data = json.loads(line)
                        log_entry = self._parse_log_entry(log_data)
                        if log_entry:
                            self.log_buffer.append(log_entry)
                            
                            # Flush buffer if full
                            if len(self.log_buffer) >= self.buffer_size:
                                await self._flush_buffer()
                                
                    except json.JSONDecodeError:
                        # Handle non-JSON log lines
                        log_entry = self._parse_text_log_line(line)
                        if log_entry:
                            self.log_buffer.append(log_entry)
                            
        except Exception as e:
            logger.error(f"Error processing log file {log_file}: {e}")
            
    def _parse_log_entry(self, log_data: Dict[str, Any]) -> Optional[LogEntry]:
        """Parse log entry from JSON data."""
        try:
            return LogEntry(
                timestamp=log_data.get('timestamp', datetime.utcnow().isoformat()),
                level=log_data.get('level', 'INFO'),
                service=log_data.get('service', 'unknown'),
                component=log_data.get('component', 'unknown'),
                correlation_id=log_data.get('correlation_id', 'N/A'),
                message=log_data.get('message', ''),
                extra_data={k: v for k, v in log_data.items() 
                           if k not in ['timestamp', 'level', 'service', 'component', 
                                      'correlation_id', 'message']}
            )
        except Exception as e:
            logger.error(f"Error parsing log entry: {e}")
            return None
            
    def _parse_text_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse log entry from text line."""
        # Simple text log parsing - can be enhanced based on format
        parts = line.split(' - ', 4)
        if len(parts) >= 4:
            return LogEntry(
                timestamp=parts[0] if parts[0] else datetime.utcnow().isoformat(),
                level=parts[2] if len(parts) > 2 else 'INFO',
                service='unknown',
                component=parts[1] if len(parts) > 1 else 'unknown',
                correlation_id='N/A',
                message=parts[-1] if parts else line
            )
        else:
            return LogEntry(
                timestamp=datetime.utcnow().isoformat(),
                level='INFO',
                service='unknown',
                component='unknown',
                correlation_id='N/A',
                message=line
            )
            
    async def _flush_buffer(self) -> None:
        """Flush log buffer to aggregated file."""
        if not self.log_buffer:
            return
            
        try:
            with open(self.aggregated_file, 'a') as f:
                for log_entry in self.log_buffer:
                    f.write(json.dumps(log_entry.to_dict()) + '\n')
                    
            logger.info(f"Flushed {len(self.log_buffer)} log entries to {self.aggregated_file}")
            self.log_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing log buffer: {e}")
            
    async def search_logs(self, query: LogQuery) -> AsyncIterator[LogEntry]:
        """Search logs based on query parameters."""
        # Ensure buffer is flushed
        await self._flush_buffer()
        
        if not self.aggregated_file.exists():
            return
            
        count = 0
        try:
            with open(self.aggregated_file, 'r') as f:
                for line in f:
                    if count >= query.limit:
                        break
                        
                    try:
                        log_data = json.loads(line.strip())
                        log_entry = LogEntry(**log_data)
                        
                        if self._matches_query(log_entry, query):
                            yield log_entry
                            count += 1
                            
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Error parsing log line: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            
    def _matches_query(self, log_entry: LogEntry, query: LogQuery) -> bool:
        """Check if log entry matches query criteria."""
        # Time range filter
        if query.start_time or query.end_time:
            try:
                entry_time = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
                if query.start_time and entry_time < query.start_time:
                    return False
                if query.end_time and entry_time > query.end_time:
                    return False
            except ValueError:
                # Skip entries with invalid timestamps
                return False
                
        # Service filter
        if query.services and log_entry.service not in query.services:
            return False
            
        # Level filter
        if query.levels and log_entry.level not in query.levels:
            return False
            
        # Correlation ID filter
        if query.correlation_id and log_entry.correlation_id != query.correlation_id:
            return False
            
        # Message content filter
        if query.message_contains and query.message_contains.lower() not in log_entry.message.lower():
            return False
            
        return True
        
    async def get_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of logs for the specified time period."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        query = LogQuery(start_time=start_time, end_time=end_time, limit=100000)
        
        summary = {
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'total_entries': 0,
            'by_level': {},
            'by_service': {},
            'by_component': {},
            'error_count': 0,
            'warning_count': 0
        }
        
        async for log_entry in self.search_logs(query):
            summary['total_entries'] += 1
            
            # Count by level
            level = log_entry.level
            summary['by_level'][level] = summary['by_level'].get(level, 0) + 1
            
            # Count by service
            service = log_entry.service
            summary['by_service'][service] = summary['by_service'].get(service, 0) + 1
            
            # Count by component
            component = log_entry.component
            summary['by_component'][component] = summary['by_component'].get(component, 0) + 1
            
            # Count errors and warnings
            if level == 'ERROR':
                summary['error_count'] += 1
            elif level == 'WARNING':
                summary['warning_count'] += 1
                
        return summary
        
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self._flush_buffer()