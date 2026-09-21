class ConversationStore:
    def __init__(self):
        self.sessions = {}

    def get(self, session_id):
        return self.sessions.get(
            session_id,
            {}
        )

    def update(self, session_id, data):
        self.sessions[session_id] = data

    def clear(self, session_id):
        self.sessions.pop(
            session_id,
            None
        )