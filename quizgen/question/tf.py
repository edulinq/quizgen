import quizgen.common
import quizgen.constants
import quizgen.question.base

class TF(quizgen.question.base.Question, question_type = quizgen.constants.QUESTION_TYPE_TF):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        if (isinstance(self.answers, bool)):
            # Change answers to look like multiple choice.
            self.answers = [
                {"correct": self.answers, "text": 'True'},
                {"correct": (not self.answers), "text": 'False'},
            ]
        elif (isinstance(self.answers, list)):
            pass
        else:
            raise quizgen.common.QuizValidationError(f"'answers' value must be a boolean, found '{self.answers}' ({type(self.answers)}).")

        self._validate_self_answer_list()

        if (len(self.answers) != 2):
            raise quizgen.common.QuizValidationError("Expecting exactly two answers, found %d." % (len(self.answers)))

        labels = list(sorted([answer.text for answer in self.answers]))

        expected = ['False', 'True']
        if (labels != expected):
            raise quizgen.common.QuizValidationError("T/F labels (text) not as expected. Expected: '%s', Actual: '%s'." % (expected, labels))

    def _shuffle(self, rng):
        self._shuffle_answers_list(rng)
