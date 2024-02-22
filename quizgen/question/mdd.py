import quizgen.common
import quizgen.constants
import quizgen.parser
import quizgen.question.base

class MDD(quizgen.question.base.Question, question_type = quizgen.constants.QUESTION_TYPE_MDD):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_answers(self):
        self._check_type(self.answers, dict, "'answers' key")

        if (len(self.answers) == 0):
            raise quizgen.common.QuizValidationError("No answers provided, at least one answer required.")

        self.answers_documents = {}

        for (key, answers) in self.answers.items():
            key_doc = quizgen.parser.parse_text(key, base_dir = self.base_dir)
            values_docs = self._validate_answer_list(answers, self.base_dir, min_correct = 1, max_correct = 1)

            self.answers_documents[key] = {
                'key': key_doc,
                'values': values_docs,
            }

    def _shuffle(self, rng):
        for key in self.answers:
            collection = list(zip(self.answers[key], self.answers_documents[key]['values']))
            rng.shuffle(collection)
            self.answers[key], self.answers_documents[key]['values'] = map(list, zip(*collection))
