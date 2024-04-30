import quizgen.common
import quizgen.constants
import quizgen.question.base

class TextOnly(quizgen.question.base.Question, question_type = quizgen.constants.QUESTION_TYPE_TEXT_ONLY):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        if (self.answers is not None):
            raise quizgen.common.QuizValidationError("'answers' key must be missing or None/null, found: '%s'." % (
                    str(self.answers)))
