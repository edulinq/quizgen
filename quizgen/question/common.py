import quizgen.common
import quizgen.parser.common

class ParsedTextWithFeedback(quizgen.parser.common.ParsedText):
    def __init__(self, parsed_text, feedback = None):
        super().__init__(parsed_text.text, parsed_text.document)

        if ((feedback is not None) and (not isinstance(feedback, quizgen.parser.common.ParsedText))):
            raise quizgen.common.QuizValidationError("Text feedback must be quizgen.parser.common.ParsedText, found '%s'." % (str(type(feedback))))

        self.feedback = feedback

    def has_feedback(self):
        return (self.feedback is not None)

    def to_pod(self, skip_feedback = False, force_dict = False, **kwargs):
        if (skip_feedback or (self.feedback is None)):
            if (force_dict):
                return {'text': self.text}
            else:
                return self.text

        return {
            'text': self.text,
            'feedback': self.feedback.to_pod(),
        }

class ParsedTextChoice(ParsedTextWithFeedback):
    def __init__(self, parsed_text_with_feedback, correct):
        super().__init__(parsed_text_with_feedback, feedback = parsed_text_with_feedback.feedback)

        if (not isinstance(correct, bool)):
            raise quizgen.common.QuizValidationError("Choice 'correct' field must be boolean, found '%s'." % (str(type(correct))))

        self.correct = correct

    def is_correct(self):
        return self.correct

    def to_pod(self, **kwargs):
        value = super().to_pod(force_dict = True, **kwargs)
        value['correct'] = self.correct
        return value
