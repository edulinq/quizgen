import abc
import copy
import importlib
import json
import logging
import math
import os
import pkgutil
import random

import json5

import quizgen.common
import quizgen.parser
import quizgen.util.file

PROMPT_FILENAME = 'prompt.md'
BASE_MODULE_NAME = 'quizgen.question'
THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

class Question(abc.ABC):
    # {question_type: class, ...}
    _types = {}
    _imported_this_package = False

    def __init_subclass__(cls, question_type = None, **kwargs):
        """
        Register question subclasses (types).
        """

        super().__init_subclass__(**kwargs)

        if (question_type is None):
            raise quizgen.common.QuizValidationError("No question type provided for question subclass.")

        cls._types[question_type] = cls

    def __init__(self, prompt = '', question_type = '', answers = None,
            base_dir = '.',
            points = 0, base_name = '',
            shuffle_answers = True,
            custom_header = None, skip_numbering = None,
            hints = None,
            **kwargs):
        self.base_dir = base_dir

        self.prompt = prompt
        self.prompt_document = None

        self.question_type = question_type

        self.answers = answers
        self.answers_documents = None

        self.points = points
        self.base_name = base_name

        self.hints = hints

        self.shuffle_answers = shuffle_answers

        self.custom_header = custom_header
        self.skip_numbering = skip_numbering

        try:
            self.validate()
        except Exception as ex:
            raise quizgen.common.QuizValidationError(f"Error while validating question (type: '%s', directory: '%s')." % (self.question_type, self.base_dir)) from ex

    def validate(self):
        if ((self.prompt is None) or (self.prompt == "")):
            raise quizgen.common.QuizValidationError("Prompt cannot be empty.")
        self.prompt_document = quizgen.parser.parse_text(self.prompt, base_dir = self.base_dir)

        if (self.hints is None):
            self.hints = {}

        self.validate_answers()

    @abc.abstractmethod
    def validate_answers(self):
        pass

    def inherit_from_group(self, group):
        """
        Inherit attributes from a group.
        """

        self.points = group.points
        self.base_name = group.name

        if (group.custom_header is not None):
            self.custom_header = group.custom_header

        if (group.skip_numbering is not None):
            self.skip_numbering = group.skip_numbering

        self.shuffle_answers = (self.shuffle_answers and group.shuffle_answers)

        for (key, value) in group.hints.items():
            # Only take hints not already set in the question.
            if (key not in self.hints):
                self.hints[key] = value

    def to_json(self, indent = 4, include_docs = True):
        return json.dumps(self.to_dict(include_docs = include_docs), indent = indent)

    def to_dict(self, include_docs = True):
        value = self.__dict__.copy()

        value['answers'] = self._answers_to_dict(self.answers)

        if (include_docs):
            value['prompt_document'] = self.prompt_document.to_pod()
            value['answers_documents'] = self._answers_to_dict(self.answers_documents)
        else:
            value.pop('prompt_document', None)
            value.pop('answers_documents', None)

        return value

    def _answers_to_dict(self, target):
        if (isinstance(target, dict)):
            return {key: self._answers_to_dict(value) for (key, value) in target.items()}
        elif (isinstance(target, list)):
            return [self._answers_to_dict(answer) for answer in target]
        elif (isinstance(target, quizgen.parser.ParseNode)):
            return target.to_pod()
        else:
            return target

    def collect_file_paths(self):
        paths = []

        paths += self.prompt_document.collect_file_paths(self.base_dir)

        for document in self._collect_documents(self.answers):
            paths += document.collect_file_paths(self.base_dir)

        return paths

    def _collect_documents(self, target):
        if (isinstance(target, dict)):
            return self._collect_documents(list(target.values()))
        elif (isinstance(target, list)):
            documents = []
            for value in target:
                documents += self._collect_documents(value)
            return documents
        elif (isinstance(target, quizgen.parser.ParseNode)):
            return [target]
        else:
            return []

    def should_skip_numbering(self):
        return ((self.skip_numbering is not None) and (self.skip_numbering))

    def copy(self):
        return copy.deepcopy(self)

    def shuffle(self, rng = None):
        if (not self.shuffle_answers):
            return

        if (rng is None):
            rng = random.Random()

        self._shuffle(rng)

    def _shuffle(self, rng):
        """
        Shuffle the answers for this question.
        By default (this method), no shuffling is performed.
        Children can override this method to support shuffling.
        """

        pass

    def _shuffle_answers_list(self, rng):
        """
        A shuffle method for question types that are a simple list.
        """

        collection = list(zip(self.answers, self.answers_documents))
        rng.shuffle(collection)
        self.answers, self.answers_documents = map(list, zip(*collection))

    @staticmethod
    def from_dict(data, base_dir = None):
        data = data.copy()

        if (base_dir is not None):
            data['base_dir'] = base_dir
        elif ('base_dir' not in data):
            data['base_dir'] = '.'

        # Documents will be parsed.
        data.pop('prompt_document', None)
        data.pop('answers_documents', None)

        question_class = Question._fetch_question_class(data.get('question_type'))
        return question_class(**data)

    @staticmethod
    def from_path(path):
        with open(path, 'r') as file:
            data = json5.load(file)

        # Check for a prompt file.
        prompt_path = os.path.join(os.path.dirname(path), PROMPT_FILENAME)
        if (os.path.exists(prompt_path)):
            logging.debug("Loading question prompt from '%s'.", prompt_path)
            data['prompt'] = quizgen.util.file.read(prompt_path)

        base_dir = os.path.dirname(path)

        return Question.from_dict(data, base_dir = base_dir)

    @staticmethod
    def _fetch_question_class(question_type):
        if (not Question._imported_this_package):
            for _, base_name, is_package in pkgutil.iter_modules([THIS_DIR]):
                if (is_package):
                    continue

                module_name = BASE_MODULE_NAME + '.' + base_name
                importlib.import_module(module_name)

            _imported_this_package = True

        if (question_type not in Question._types):
            raise quizgen.common.QuizValidationError("Unknown question type: '%s'." % (str(question_type)))

        return Question._types[question_type]

    def _validate_self_answer_list(self, min_correct = 0, max_correct = math.inf):
        self.answers_documents = self._validate_answer_list(self.answers, self.base_dir,
                min_correct = min_correct, max_correct = max_correct)

    def _validate_answer_list(self, answers, base_dir, min_correct = 0, max_correct = math.inf):
        self._check_type(answers, list, "'answers'")

        if (len(answers) == 0):
            raise quizgen.common.QuizValidationError(f"No answers provided, at least one answer required.")

        num_correct = 0
        for answer in answers:
            if ('correct' not in answer):
                raise quizgen.common.QuizValidationError(f"Answer has no 'correct' field.")

            if ('text' not in answer):
                raise quizgen.common.QuizValidationError(f"Answer has no 'text' field.")

            if (answer['correct']):
                num_correct += 1

        if (num_correct < min_correct):
            raise quizgen.common.QuizValidationError(f"Did not find enough correct answers. Expected at least {min_correct}, found {num_correct}.")

        if (num_correct > max_correct):
            raise quizgen.common.QuizValidationError(f"Found too many correct answers. Expected at most {max_correct}, found {num_correct}.")

        answers_documents = []
        for answer in answers:
            doc = quizgen.parser.parse_text(answer['text'], base_dir = base_dir)
            answers_documents.append(doc)

        return answers_documents

    def _validate_text_answers(self):
        if (self.answers is None):
            self.answers = ['']
        elif (isinstance(self.answers, str)):
            self.answers = [self.answers]

        if (not isinstance(self.answers, list)):
            possible_answers = 'null/None, string, empty list, or list of strings'
            raise quizgen.common.QuizValidationError("Question type '%s' must an answer that is %s, found: '%s'." % (
                    self.question_type, possible_answers, str(self.answers)))

        if (len(self.answers) == 0):
            self.answers = ['']

        for i in range(len(self.answers)):
            answer = self.answers[i]
            if (not isinstance(answer, str)):
                raise quizgen.common.QuizValidationError("Question type '%s' answers must be a list of strings, element %d is '%s' (%s)." % (
                        self.question_type, i, answer, str(type(answer))))

        self.answers_documents = []
        for answer in self.answers:
            self.answers_documents.append(quizgen.parser.parse_text(answer, base_dir = self.base_dir))

    def _validate_fimb_answers(self):
        self._check_type(self.answers, dict, "'answers' key")

        if (len(self.answers) == 0):
            raise quizgen.common.QuizValidationError("Expected 'answers' dict to be non-empty.")

        for (key, values) in self.answers.items():
            if (not isinstance(values, list)):
                self.answers[key] = [values]

        for (key, values) in self.answers.items():
            self._check_type(key, str, "key in 'answers' dict")

            if (len(values) == 0):
                raise quizgen.common.QuizValidationError("Expected possible values to be non-empty.")

            for value in values:
                self._check_type(value, str, "value in 'answers' dict")

        self.answers_documents = {}
        for (key, values) in self.answers.items():
            key_doc = quizgen.parser.parse_text(key, base_dir = self.base_dir)

            values_docs = []
            for value in values:
                values_docs.append(quizgen.parser.parse_text(value, base_dir = self.base_dir))

            self.answers_documents[key] = {
                'key': key_doc,
                'values': values_docs,
            }

    def _check_type(self, value, expected_type, label):
        if (not isinstance(value, expected_type)):
            raise quizgen.common.QuizValidationError(f"{label} must be a {expected_type}, found '{value}' ({type(value)}).")
