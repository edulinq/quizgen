import quizgen.common
import quizgen.constants
import quizgen.parser
import quizgen.question.base

class Matching(quizgen.question.base.Question, question_type = quizgen.constants.QUESTION_TYPE_MATCHING):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_answers(self):
        self._check_type(self.answers, dict, "'answers' key")

        if ('matches' not in self.answers):
            raise quizgen.common.QuizValidationError("Matching 'answers' value is missing the 'matches' field.")

        for i in range(len(self.answers['matches'])):
            match = self.answers['matches'][i]
            if (len(match) != 2):
                raise quizgen.common.QuizValidationError(f"Expected exactly two items for a match list, found {len(match)} items at element {i}.")

        if ('distractors' not in self.answers):
            self.answers['distractors'] = []

        for i in range(len(self.answers['distractors'])):
            distractor = self.answers['distractors'][i]
            if (not isinstance(distractor, str)):
                raise quizgen.common.QuizValidationError(f"Distractors must be strings, found {type(distractor)} at element {i}.")

            distractor = distractor.strip()

            if ("\n" in distractor):
                raise quizgen.common.QuizValidationError(f"Distractors cannot have newlines, found {type(distractor)} at element {i}.")

            self.answers['distractors'][i] = distractor

        self.answers_documents = {
            'matches': [],
            'distractors': [],
        }

        for (left, right) in self.answers['matches']:
            left_doc = quizgen.parser.parse_text(left, base_dir = self.base_dir)
            right_doc = quizgen.parser.parse_text(right, base_dir = self.base_dir)

            self.answers_documents['matches'].append([left_doc, right_doc])

        for distractor in self.answers['distractors']:
            doc = quizgen.parser.parse_text(distractor, base_dir = self.base_dir)
            self.answers_documents['distractors'].append(doc)

    def _shuffle(self, rng):
        # Shuffling matching is special because it requires additional shuffling support at the converter level.
        self.answers['shuffle'] = True
        self.answers['shuffle_seed'] = rng.randint(0, 2 ** 64)
