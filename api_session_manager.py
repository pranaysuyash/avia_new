"""
Simple session manager for API testing
"""

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.results = {}
    
    def set_session_data(self, user_id, data):
        """Store session data for a user"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {}
        self.sessions[user_id].update(data)
    
    def get_session_data(self, user_id):
        """Get session data for a user"""
        return self.sessions.get(user_id, {})
    
    def store_result(self, user_id, result):
        """Store a transcription result"""
        if user_id not in self.results:
            self.results[user_id] = []
        self.results[user_id].append(result)
    
    def get_stored_results(self, user_id):
        """Get stored results for a user"""
        return self.results.get(user_id, [])