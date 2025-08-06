"""
Transcription Service
Mock implementation to get API running
"""

class TranscriptionService:
    """Mock transcription service"""
    
    def __init__(self, db=None):
        self.db = db
    
    def get_transcript(self, transcript_id, user_id):
        """Get transcript by ID"""
        return None
    
    def create_transcript(self, data):
        """Create new transcript"""
        return {"id": "mock-id", "status": "pending"}
    
    def update_transcript(self, transcript_id, data):
        """Update transcript"""
        return {"id": transcript_id, "status": "updated"}
    
    def delete_transcript(self, transcript_id):
        """Delete transcript"""
        return True