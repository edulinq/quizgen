import glob
import os

import quizgen.common
import quizgen.question

QUESTION_FILENAME = 'question.json'

class Group(object):
    def __init__(self, name = '',
            pick_count = 1, points = 10,
            questions = [], **kwargs):
        self.name = name
        self.pick_count = pick_count
        self.points = points

        self.questions = questions

        try:
            self.validate()
        except Exception as ex:
            raise quizgen.common.QuizValidationError(f"Error while validating group.") from ex

    def validate(self):
        if ((self.name is None) or (self.name == "")):
            raise quizgen.common.QuizValidationError("Name cannot be empty.")

        for question in self.questions:
            question.points = self.points
            question.base_name = self.name

    def to_dict(self, include_docs = True):
        value = self.__dict__.copy()
        value['questions'] = [question.to_dict(include_docs = include_docs) for question in self.questions]
        return value

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

    def copy_questions(self):
        return [question.copy() for question in self.questions]

    def choose_questions(self, rng):
        return [question.copy() for question in rng.choices(self.questions, k = self.pick_count)]

def _parse_questions(path):
    if (not os.path.exists(path)):
        raise quizgen.common.QuizValidationError(f"Question path does not exist: '{path}'.")

    if (os.path.isfile(path)):
        return [quizgen.question.Question.from_path(path)]

    questions = []
    for subpath in sorted(glob.glob(os.path.join(path, '**', QUESTION_FILENAME), recursive = True)):
        questions.append(quizgen.question.Question.from_path(subpath))

    return questions
