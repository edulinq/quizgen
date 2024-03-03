import glob
import logging
import os

import quizgen.common
import quizgen.question.base

QUESTION_FILENAME = 'question.json'

class Group(object):
    def __init__(self, name = '',
            pick_count = 1, points = 10,
            shuffle_answers = True, pick_with_replacement = True,
            custom_header = None, skip_numbering = None,
            hints = None, hints_first = None, hints_last = None,
            questions = [], **kwargs):
        self.name = name
        self.pick_count = pick_count
        self.points = points

        self.shuffle_answers = shuffle_answers
        self.pick_with_replacement = pick_with_replacement
        self._used_question_indexes = set()

        self.custom_header = custom_header
        self.skip_numbering = skip_numbering

        self.hints = hints
        self.hints_first = hints_first
        self.hints_last = hints_last

        self.questions = questions

        try:
            self.validate()
        except Exception as ex:
            raise quizgen.common.QuizValidationError(f"Error while validating group (%s)." % (self.name)) from ex

    def validate(self):
        if ((self.name is None) or (self.name == "")):
            raise quizgen.common.QuizValidationError("Name cannot be empty.")

        if (self.pick_count < 0):
            raise quizgen.common.QuizValidationError("Pick count cannot be negative.")

        if (self.hints is None):
            self.hints = {}

        if (self.hints_first is None):
            self.hints_first = {}

        if (self.hints_last is None):
            self.hints_last = {}

        if (not isinstance(self.questions, list)):
            raise quizgen.common.QuizValidationError("Questions must be a non-empty list, found: '%s'." % (str(self.questions)))

        if (len(self.questions) == 0):
            raise quizgen.common.QuizValidationError("Questions must be non-empty.")

        for question in self.questions:
            question.inherit_from_group(self)

    def to_dict(self, include_docs = True):
        value = self.__dict__.copy()
        value['questions'] = [question.to_dict(include_docs = include_docs) for question in self.questions]
        return value

    def should_skip_numbering(self):
        return ((self.skip_numbering is not None) and (self.skip_numbering))

    def collect_file_paths(self):
        paths = []

        for question in self.questions:
            paths += question.collect_file_paths()

        return paths

    @staticmethod
    def from_dict(group_info, base_dir):
        group_info = group_info.copy()

        paths = []
        for path in group_info.get('questions', []):
            if (not os.path.isabs(path)):
                path = os.path.join(base_dir, path)
            paths.append(os.path.abspath(path))

        paths = list(sorted(set(paths)))

        questions = []
        for path in paths:
            questions += _parse_questions(path)

        group_info['questions'] = questions

        return Group(**group_info)

    def choose_questions(self, all_questions = False, rng = None, with_replacement = True):
        if ((self.pick_count == 0) or (len(self.questions) == 0)):
            logging.warning("Group '%s' will select no questions (pick_count: %d, group size: %d)." % (
                    self.name, self.pick_count, len(self.questions)))
            return []

        with_replacement = (self.pick_with_replacement and with_replacement)

        if (rng is None):
            seed = random.randint(0, 2**64)
            rng = random.Random(seed)

        count = self.pick_count
        if (all_questions):
            count = len(self.questions)

        if (count > len(self.questions)):
            logging.warning("Group '%s' was asked to pick more questions than available (pick_count: %d, group size: %d)." % (
                    self.name, count, len(self.questions)))
            count = len(self.questions)

        questions = self._choose_questions(count, rng, with_replacement)

        # Rename questions if there are more than one.
        if (len(questions) > 1):
            for i in range(len(questions)):
                questions[i].name = "%s - %d" % (self.name, i + 1)

        # Inherit position-specific hints.
        questions[0].add_hints(self.hints_first)
        questions[-1].add_hints(self.hints_last)

        return questions

    def _choose_questions(self, count, rng, with_replacement):
        indexes = list(range(len(self.questions)))

        if (not with_replacement):
            indexes = list(set(indexes) - self._used_question_indexes)

            if (count > len(indexes)):
                logging.warning("Group '%s' does not have enough questions to pick without replacement." % (self.name))
                # Reset the selection pool.
                indexes = list(range(len(self.questions)))
                self._used_question_indexes = set()

        rng.shuffle(indexes)
        indexes = indexes[:count]

        if (not with_replacement):
            self._used_question_indexes |= set(indexes)

        return [self.questions[index].copy() for index in indexes]

def _parse_questions(path):
    if (not os.path.exists(path)):
        raise quizgen.common.QuizValidationError(f"Question path does not exist: '{path}'.")

    if (os.path.isfile(path)):
        return [quizgen.question.base.Question.from_path(path)]

    questions = []
    for subpath in sorted(glob.glob(os.path.join(path, '**', QUESTION_FILENAME), recursive = True)):
        questions.append(quizgen.question.base.Question.from_path(subpath))

    return questions
