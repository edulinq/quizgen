import json

import quizgen.common

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

    def to_json(self, indent = 4, include_docs = True):
        return json.dumps(self.to_dict(include_docs = include_docs), indent = indent)

    def num_questions(self):
        return len(self.questions)
