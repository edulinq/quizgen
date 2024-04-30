import quizgen.constants
import quizgen.question.base

class SA(quizgen.question.base.Question, question_type = quizgen.constants.QUESTION_TYPE_SA):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        self._validate_text_answers()
