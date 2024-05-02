import quizgen.util.serial

class ParsedText(quizgen.util.serial.PODSerializer):
    """
    A representation of text that has been successfully parsed.
    """

    def __init__(self, text, document):
        self.text = text
        self.document = document

    def to_pod(self, **kwargs):
        return self.text
