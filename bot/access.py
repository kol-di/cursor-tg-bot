class User:
    def __init__(self, nickname):
        self._nickname = nickname
    
    def is_authorized(self):
        return True