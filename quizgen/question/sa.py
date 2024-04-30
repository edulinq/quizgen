import quizgen.constants
import quizgen.question.base

class Essay(quizgen.question.base.Question, question_type = quizgen.constants.QUESTION_TYPE_ESSAY):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        self._validate_text_answers()
