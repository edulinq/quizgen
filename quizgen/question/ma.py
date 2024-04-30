import quizgen.constants
import quizgen.question.base

class MA(quizgen.question.base.Question, question_type = quizgen.constants.QUESTION_TYPE_MA):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        self._validate_self_answer_list()

    def _shuffle(self, rng):
        self._shuffle_answers_list(rng)
