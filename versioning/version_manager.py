"""
Version control manager for transcripts with sophisticated conflict resolution
"""

import difflib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Set
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from database.models import Transcript, TranscriptVersion, User
import json
import re


class ConflictResolution:
    """Handles three-way merge and conflict resolution"""
    
    @staticmethod
    def three_way_merge(
        base_text: str,
        current_text: str,
        incoming_text: str
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Perform a three-way merge between base, current, and incoming versions
        Returns: (merged_text, conflicts, has_conflicts)
        """
        base_lines = base_text.splitlines(keepends=True)
        current_lines = current_text.splitlines(keepends=True)
        incoming_lines = incoming_text.splitlines(keepends=True)
        
        # Get diffs
        base_to_current = list(difflib.ndiff(base_lines, current_lines))
        base_to_incoming = list(difflib.ndiff(base_lines, incoming_lines))
        
        merged_lines = []
        conflicts = []
        has_conflicts = False
        
        i = 0
        while i < max(len(base_to_current), len(base_to_incoming)):
            if i < len(base_to_current):
                current_line = base_to_current[i]
            else:
                current_line = None
                
            if i < len(base_to_incoming):
                incoming_line = base_to_incoming[i]
            else:
                incoming_line = None
            
            # Both unchanged
            if current_line and incoming_line and current_line[0] == ' ' and incoming_line[0] == ' ':
                merged_lines.append(current_line[2:])
            
            # Only current changed
            elif current_line and current_line[0] in '+-' and (not incoming_line or incoming_line[0] == ' '):
                if current_line[0] == '+':
                    merged_lines.append(current_line[2:])
                # Skip deletions
            
            # Only incoming changed
            elif incoming_line and incoming_line[0] in '+-' and (not current_line or current_line[0] == ' '):
                if incoming_line[0] == '+':
                    merged_lines.append(incoming_line[2:])
                # Skip deletions
            
            # Both changed - conflict
            elif (current_line and current_line[0] in '+-') and (incoming_line and incoming_line[0] in '+-'):
                has_conflicts = True
                conflict_start = len(merged_lines)
                
                # Add conflict markers
                merged_lines.append("<<<<<<< CURRENT\n")
                if current_line[0] == '+':
                    merged_lines.append(current_line[2:])
                merged_lines.append("=======\n")
                if incoming_line[0] == '+':
                    merged_lines.append(incoming_line[2:])
                merged_lines.append(">>>>>>> INCOMING\n")
                
                conflicts.append({
                    'line': conflict_start,
                    'current': current_line[2:] if current_line else '',
                    'incoming': incoming_line[2:] if incoming_line else ''
                })
            
            i += 1
        
        return ''.join(merged_lines), conflicts, has_conflicts
    
    @staticmethod
    def auto_resolve_conflicts(
        merged_text: str,
        conflicts: List[Dict[str, Any]],
        strategy: str = 'smart'
    ) -> str:
        """
        Automatically resolve conflicts based on strategy
        Strategies: 'current', 'incoming', 'smart'
        """
        if strategy == 'current':
            # Keep current version for all conflicts
            merged_text = re.sub(
                r'<<<<<<< CURRENT\n(.*?)\n=======\n.*?\n>>>>>>> INCOMING\n',
                r'\1',
                merged_text,
                flags=re.DOTALL
            )
        elif strategy == 'incoming':
            # Keep incoming version for all conflicts
            merged_text = re.sub(
                r'<<<<<<< CURRENT\n.*?\n=======\n(.*?)\n>>>>>>> INCOMING\n',
                r'\1',
                merged_text,
                flags=re.DOTALL
            )
        elif strategy == 'smart':
            # Smart resolution based on content analysis
            for conflict in conflicts:
                current = conflict['current'].strip()
                incoming = conflict['incoming'].strip()
                
                # If one is empty, take the non-empty one
                if not current and incoming:
                    merged_text = merged_text.replace(
                        f"<<<<<<< CURRENT\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> INCOMING\n",
                        incoming + '\n'
                    )
                elif current and not incoming:
                    merged_text = merged_text.replace(
                        f"<<<<<<< CURRENT\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> INCOMING\n",
                        current + '\n'
                    )
                # If both have content, prefer the longer one (more information)
                elif len(incoming) > len(current) * 1.5:
                    merged_text = merged_text.replace(
                        f"<<<<<<< CURRENT\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> INCOMING\n",
                        incoming + '\n'
                    )
                else:
                    # Keep current by default
                    merged_text = merged_text.replace(
                        f"<<<<<<< CURRENT\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> INCOMING\n",
                        current + '\n'
                    )
        
        return merged_text


class VersionManager:
    """Manages version control for transcripts"""
    
    def __init__(self, session: Session):
        self.session = session
        self.conflict_resolver = ConflictResolution()
    
    def create_version(
        self,
        transcript_id: int,
        user_id: int,
        change_summary: str,
        content: Optional[str] = None,
        entities: Optional[Dict] = None,
        summary: Optional[str] = None
    ) -> TranscriptVersion:
        """Create a new version of a transcript"""
        # Get the transcript
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        if not transcript:
            raise ValueError("Transcript not found")
        
        # Get the latest version number
        latest_version = self.session.query(
            func.max(TranscriptVersion.version_number)
        ).filter_by(transcript_id=transcript_id).scalar() or 0
        
        # If no content provided, use current transcript content
        if content is None:
            content = transcript.content
        if entities is None:
            entities = transcript.entities
        if summary is None:
            summary = transcript.summary
        
        # Create new version
        version = TranscriptVersion(
            transcript_id=transcript_id,
            version_number=latest_version + 1,
            content=content,
            entities=entities,
            summary=summary,
            changed_by_id=user_id,
            change_summary=change_summary
        )
        
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        
        return version
    
    def get_versions(
        self,
        transcript_id: int,
        limit: Optional[int] = None
    ) -> List[TranscriptVersion]:
        """Get all versions of a transcript"""
        query = self.session.query(TranscriptVersion).options(
            joinedload(TranscriptVersion.changed_by)
        ).filter_by(
            transcript_id=transcript_id
        ).order_by(desc(TranscriptVersion.version_number))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_version(
        self,
        transcript_id: int,
        version_number: int
    ) -> Optional[TranscriptVersion]:
        """Get a specific version of a transcript"""
        return self.session.query(TranscriptVersion).options(
            joinedload(TranscriptVersion.changed_by)
        ).filter_by(
            transcript_id=transcript_id,
            version_number=version_number
        ).first()
    
    def get_latest_version(self, transcript_id: int) -> Optional[TranscriptVersion]:
        """Get the latest version of a transcript"""
        return self.session.query(TranscriptVersion).options(
            joinedload(TranscriptVersion.changed_by)
        ).filter_by(
            transcript_id=transcript_id
        ).order_by(desc(TranscriptVersion.version_number)).first()
    
    def update_transcript(
        self,
        transcript_id: int,
        user_id: int,
        new_content: str,
        change_summary: str,
        new_entities: Optional[Dict] = None,
        new_summary: Optional[str] = None,
        base_version_number: Optional[int] = None,
        conflict_strategy: str = 'smart',
        notification_manager=None  # Optional notification manager
    ) -> Tuple[Transcript, TranscriptVersion, Dict[str, Any]]:
        """
        Update a transcript and create a new version with conflict resolution
        Returns: (transcript, version, conflict_info)
        """
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        if not transcript:
            raise ValueError("Transcript not found")
        
        conflict_info = {
            'has_conflicts': False,
            'conflicts': [],
            'resolution_strategy': None,
            'base_version': base_version_number
        }
        
        # Check for conflicts if base version provided
        if base_version_number is not None:
            latest_version = self.get_latest_version(transcript_id)
            if latest_version and latest_version.version_number > base_version_number:
                # Three-way merge needed
                base_version = self.get_version(transcript_id, base_version_number)
                if base_version:
                    merged_content, conflicts, has_conflicts = self.conflict_resolver.three_way_merge(
                        base_text=base_version.content,
                        current_text=transcript.content,
                        incoming_text=new_content
                    )
                    
                    if has_conflicts:
                        conflict_info['has_conflicts'] = True
                        conflict_info['conflicts'] = conflicts
                        conflict_info['resolution_strategy'] = conflict_strategy
                        
                        # Auto-resolve conflicts
                        new_content = self.conflict_resolver.auto_resolve_conflicts(
                            merged_content,
                            conflicts,
                            conflict_strategy
                        )
                        change_summary = f"[Merged with conflicts] {change_summary}"
        
        # Create a version with the current state before updating
        version = self.create_version(
            transcript_id=transcript_id,
            user_id=user_id,
            change_summary=change_summary,
            content=transcript.content,  # Save current content
            entities=transcript.entities,
            summary=transcript.summary
        )
        
        # Update the transcript
        transcript.content = new_content
        if new_entities is not None:
            transcript.entities = new_entities
        if new_summary is not None:
            transcript.summary = new_summary
        transcript.word_count = len(new_content.split()) if new_content else 0
        
        self.session.commit()
        self.session.refresh(transcript)
        
        # Send notifications if manager provided
        if notification_manager:
            related_users = notification_manager.get_related_users(transcript_id)
            notification_manager.notify_transcript_edit(
                transcript_id=transcript_id,
                editor_id=user_id,
                change_summary=change_summary,
                notify_users=related_users
            )
        
        return transcript, version, conflict_info
    
    def restore_version(
        self,
        transcript_id: int,
        version_number: int,
        user_id: int
    ) -> Transcript:
        """Restore a transcript to a specific version"""
        version = self.get_version(transcript_id, version_number)
        if not version:
            raise ValueError("Version not found")
        
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        if not transcript:
            raise ValueError("Transcript not found")
        
        # Create a new version for the restore action
        self.create_version(
            transcript_id=transcript_id,
            user_id=user_id,
            change_summary=f"Restored to version {version_number}",
            content=transcript.content,  # Save current state
            entities=transcript.entities,
            summary=transcript.summary
        )
        
        # Restore the transcript to the selected version
        transcript.content = version.content
        transcript.entities = version.entities
        transcript.summary = version.summary
        transcript.word_count = len(version.content.split()) if version.content else 0
        
        self.session.commit()
        self.session.refresh(transcript)
        
        return transcript
    
    def get_diff(
        self,
        transcript_id: int,
        version1_number: int,
        version2_number: int,
        context_lines: int = 3
    ) -> Dict[str, Any]:
        """Get the diff between two versions"""
        version1 = self.get_version(transcript_id, version1_number)
        version2 = self.get_version(transcript_id, version2_number)
        
        if not version1 or not version2:
            raise ValueError("One or both versions not found")
        
        # Get text diff with context
        text_diff = list(difflib.unified_diff(
            version1.content.splitlines(keepends=True),
            version2.content.splitlines(keepends=True),
            fromfile=f"Version {version1_number}",
            tofile=f"Version {version2_number}",
            n=context_lines,
            lineterm=''
        ))
        
        # Get inline diff for better visualization
        inline_diff = []
        matcher = difflib.SequenceMatcher(
            None,
            version1.content.splitlines(),
            version2.content.splitlines()
        )
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for line in version1.content.splitlines()[i1:i2]:
                    inline_diff.append(('equal', line))
            elif tag == 'delete':
                for line in version1.content.splitlines()[i1:i2]:
                    inline_diff.append(('delete', line))
            elif tag == 'insert':
                for line in version2.content.splitlines()[j1:j2]:
                    inline_diff.append(('insert', line))
            elif tag == 'replace':
                for line in version1.content.splitlines()[i1:i2]:
                    inline_diff.append(('delete', line))
                for line in version2.content.splitlines()[j1:j2]:
                    inline_diff.append(('insert', line))
        
        # Get entity diff
        entities1 = version1.entities if isinstance(version1.entities, dict) else {}
        entities2 = version2.entities if isinstance(version2.entities, dict) else {}
        
        entity_diff = {
            'added': {},
            'removed': {},
            'modified': {}
        }
        
        all_keys = set(entities1.keys()) | set(entities2.keys())
        for key in all_keys:
            if key not in entities1:
                entity_diff['added'][key] = entities2[key]
            elif key not in entities2:
                entity_diff['removed'][key] = entities1[key]
            elif entities1[key] != entities2[key]:
                entity_diff['modified'][key] = {
                    'old': entities1[key],
                    'new': entities2[key]
                }
        
        # Calculate statistics
        lines1 = version1.content.splitlines()
        lines2 = version2.content.splitlines()
        
        stats = {
            'lines_added': sum(1 for op, _ in inline_diff if op == 'insert'),
            'lines_removed': sum(1 for op, _ in inline_diff if op == 'delete'),
            'lines_modified': sum(1 for op, _ in inline_diff if op in ('insert', 'delete')) // 2,
            'total_lines_v1': len(lines1),
            'total_lines_v2': len(lines2)
        }
        
        return {
            'text_diff': text_diff,
            'inline_diff': inline_diff,
            'entity_diff': entity_diff,
            'version1': version1,
            'version2': version2,
            'stats': stats
        }
    
    def get_version_stats(self, transcript_id: int) -> Dict[str, Any]:
        """Get statistics about versions"""
        versions = self.get_versions(transcript_id)
        
        if not versions:
            return {
                'total_versions': 0,
                'contributors': [],
                'last_modified': None,
                'most_active_contributor': None
            }
        
        # Count contributions by user
        contributor_counts = {}
        for version in versions:
            username = version.changed_by.username
            contributor_counts[username] = contributor_counts.get(username, 0) + 1
        
        return {
            'total_versions': len(versions),
            'contributors': list(contributor_counts.keys()),
            'contributor_counts': contributor_counts,
            'last_modified': versions[0].created_at if versions else None,
            'most_active_contributor': max(
                contributor_counts.items(), 
                key=lambda x: x[1]
            )[0] if contributor_counts else None
        }
    
    def search_versions(
        self,
        transcript_id: int,
        query: str
    ) -> List[TranscriptVersion]:
        """Search versions by change summary or content"""
        versions = self.session.query(TranscriptVersion).options(
            joinedload(TranscriptVersion.changed_by)
        ).filter(
            TranscriptVersion.transcript_id == transcript_id,
            (TranscriptVersion.change_summary.ilike(f'%{query}%') |
             TranscriptVersion.content.ilike(f'%{query}%'))
        ).order_by(desc(TranscriptVersion.version_number)).all()
        
        return versions
    
    def get_version_timeline(
        self,
        transcript_id: int
    ) -> List[Dict[str, Any]]:
        """Get a timeline of changes"""
        versions = self.get_versions(transcript_id)
        
        timeline = []
        for i, version in enumerate(versions):
            # Calculate content changes
            if i < len(versions) - 1:
                prev_version = versions[i + 1]
                lines_added = len(version.content.splitlines()) - len(prev_version.content.splitlines())
                words_changed = abs(len(version.content.split()) - len(prev_version.content.split()))
            else:
                # First version
                lines_added = len(version.content.splitlines())
                words_changed = len(version.content.split())
            
            timeline.append({
                'version_number': version.version_number,
                'date': version.created_at,
                'author': version.changed_by.username,
                'summary': version.change_summary,
                'lines_changed': abs(lines_added),
                'words_changed': words_changed
            })
        
        return timeline
    
    def get_active_editors(
        self,
        transcript_id: int,
        minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """Get users who have edited recently"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        recent_versions = self.session.query(TranscriptVersion).options(
            joinedload(TranscriptVersion.changed_by)
        ).filter(
            TranscriptVersion.transcript_id == transcript_id,
            TranscriptVersion.created_at >= cutoff_time
        ).all()
        
        active_editors = []
        for version in recent_versions:
            active_editors.append({
                'user': version.changed_by.username,
                'last_edit': version.created_at,
                'version': version.version_number
            })
        
        return active_editors