import datetime
import json
import os

import json5

import quizgen.question
import quizgen.common
import quizgen.parser
import quizgen.quiz

DUMMY_DATA = {
    'title': 'Dummy Title',
    'description': 'Dummy description.',
    'course_title': 'Dummy Course',
    'term_title': 'Dummy Term',
    'version': '0.0.0',
}

class Variant(object):
    """
    A quiz varint is an instantiation of a quiz with specific questions chosen for each group.
    Variants no longer have groups, just questions

    Variants should be created from quizzes, and will therefore not be deeply validated,
    just checked for null values.
    """

    def __init__(self,
            title = None,
            course_title = None, term_title = None,
            description = None, description_document = None,
            date = None,
            questions = None,
            version = None, seed = None,
            **kwargs):
        self.title = title
        self.course_title = course_title
        self.term_title = term_title
        self.date = date

        self.description = description
        self.description_document = description_document

        self.questions = questions

        self.version = version
        self.seed = seed

        self.validate()

    def validate(self):
        values = self.__dict__.copy()
        for (key, value) in values.items():
            if (value is None):
                raise quizgen.common.QuizValidationError("Empty variant value: '%s'." % (key))

    def to_dict(self, include_docs = True):
        value = self.__dict__.copy()

        if ('date' in value):
            value['date'] = value['date'].isoformat()

        value['questions'] = [question.to_dict(include_docs = include_docs) for question in self.questions]

        if (include_docs):
            value['description_document'] = self.description_document.to_pod()
        else:
            del value['description_document']

        return value

    @staticmethod
    def from_path(path, override_base_dir = False):
        path = os.path.abspath(path)

        with open(path, 'r') as file:
            data = json5.load(file)

        base_dir = None
        if (override_base_dir):
            base_dir = os.path.dirname(path)

        return Variant.from_dict(data, base_dir = base_dir)

    @staticmethod
    def from_dict(data, base_dir = None):
        data = data.copy()

        if (base_dir is not None):
            data['base_dir'] = base_dir
        elif ('base_dir' not in data):
            data['base_dir'] = '.'

        if ('date' in data):
            data['date'] = datetime.datetime.fromisoformat(data['date'])

        data['description_document'] = quizgen.parser.parse_text(data['description'], base_dir = base_dir)
        data['questions'] = [quizgen.question.Question.from_dict(question, base_dir = base_dir) for question in data['questions']]

        return Variant(**data)

    def to_json(self, indent = 4, include_docs = True):
        return json.dumps(self.to_dict(include_docs = include_docs), indent = indent)

    def num_questions(self):
        return len(self.questions)

    @staticmethod
    def get_dummy():
        """
        Get a "dummy" variant that has no real information.
        """

        return quizgen.quiz.Quiz(**DUMMY_DATA).create_variant()
