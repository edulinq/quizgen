"""
Convert a quiz to JSON.
"""

class JSONConverter(object):
    def __init__(self, **kwargs):
        super().__init__()

    def convert_quiz(self, quiz, **kwargs):
        return quiz.to_json()
