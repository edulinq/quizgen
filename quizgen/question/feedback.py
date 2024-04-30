import quizgen.parser.common

class ParsedTextWithFeedback(quizgen.parser.common.ParsedText):
    def __init__(self, parsed_text, feedback = None):
        super().__init__(parsed_text.text, parsed_text.document)
        self.feedback = feedback
