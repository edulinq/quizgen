import quizgen.common
import quizgen.constants
import quizgen.question.base

class Numerical(quizgen.question.base.Question, question_type = quizgen.constants.QUESTION_TYPE_NUMERICAL):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_answers(self):
        self._check_type(self.answers, list, "'answers' key")

        for answer in self.answers:
            label = "values of 'answers' key"
            self._check_type(answer, dict, label)

            if ('type' not in answer):
                raise quizgen.common.QuizValidationError(f"Missing key ('type') for {label}.")

            if (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_EXACT):
                required_keys = ['value']

                if ('margin' not in answer):
                    answer['margin'] = 0
            elif (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_RANGE):
                required_keys = ['min', 'max']
            elif (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_PRECISION):
                required_keys = ['value', 'precision']
            else:
                raise quizgen.common.QuizValidationError(f"Unknown numerical answer type: '{answer['type']}'.")

            for key in required_keys:
                if (key not in answer):
                    raise quizgen.common.QuizValidationError(f"Missing required key '{key}' for numerical answer type '{answer['type']}'.")
