
class LoopDetector:
    """
    Detects repeated items in a sequence to prevent infinite loops or redundant processing.
    """
    def __init__(self, history_size=10, repeat_threshold=2):
        self.history_size = history_size
        self.repeat_threshold = repeat_threshold
        self.history = []

    def add_item(self, item):
        self.history.append(item)
        if len(self.history) > self.history_size:
            self.history.pop(0)

    def is_looping(self, item):
        return self.history.count(item) >= self.repeat_threshold

    def get_recent_history(self):
        return list(self.history)
