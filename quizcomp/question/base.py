import abc
import copy
import importlib
import logging
import math
import os
import pkgutil
import random
import re

import quizcomp.common
import quizcomp.constants
import quizcomp.parser.public
import quizcomp.question.common
import quizcomp.util.dirent
import quizcomp.util.serial

BASE_MODULE_NAME = 'quizcomp.question'
THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

class Question(quizcomp.util.serial.JSONSerializer):
    # {question_type: class, ...}
    _types = {}
    _imported_this_package = False

    def __init_subclass__(cls, question_type = None, **kwargs):
        """
        Register question subclasses (types).
        """

        super().__init_subclass__(**kwargs)

        if (question_type is None):
            raise quizcomp.common.QuizValidationError("No question type provided for question subclass.")

        cls._question_type = question_type
        cls._types[question_type] = cls

    def __init__(self, type = quizcomp.constants.TYPE_QUESTION,
            prompt = '', prompt_path = None,
            question_type = None,
            answers = None,
            base_dir = '.',
            points = 0, name = '',
            shuffle_answers = True,
            custom_header = None, skip_numbering = None,
            hints = None, feedback = None,
            ids = {},
            **kwargs):
        super().__init__(type = type, **kwargs)

        self.base_dir = base_dir

        self.prompt = prompt
        self._prompt_path = prompt_path

        if (question_type is None):
            question_type = self.__class__._question_type

        self.question_type = question_type

        self.answers = answers

        self.points = points
        self.name = name

        self.hints = hints
        self.feedback = feedback

        self.shuffle_answers = shuffle_answers

        self.custom_header = custom_header
        self.skip_numbering = skip_numbering

        self.ids = ids.copy()
        self.ids['base_dir'] = base_dir

        try:
            self.validate()
        except Exception as ex:
            ids = self.ids.copy()
            ids['name'] = self.name
            ids['question_type'] = self.question_type

            raise quizcomp.common.QuizValidationError('Error while validating question.', ids = ids) from ex

    def write(self, out_dir = None, split_prompt = True):
        """
        Write out this question to the target out directory
        (or self.base_dir if the out directory is not specified).
        """

        if (out_dir is None):
            out_dir = self.base_dir

        os.makedirs(out_dir, exist_ok = True)

        question = self.copy()

        # Zero out fields we don't want to write.
        question.base_dir = None
        question.ids = {}

        if (split_prompt):
            prompt_text = question.prompt.text
            question.prompt = None

            prompt_path = os.path.join(out_dir, quizcomp.constants.PROMPT_FILENAME)
            quizcomp.util.dirent.write_file(prompt_path, prompt_text)

        out_path = os.path.join(out_dir, quizcomp.constants.QUESTION_FILENAME)
        question.to_path(out_path)

    def _validate(self):
        self._validate_prompt()
        self._validate_question_feedback()
        self._validate_answers()

        if (self.hints is None):
            self.hints = {}
        else:
            self._check_type(self.hints, dict, "'hints'")

    @abc.abstractmethod
    def _validate_answers(self):
        pass

    def _validate_prompt(self):
        """
        The prompt is allowed to appear (in order of priority):
        in the prompt field, be pointed to by the _prompt_path member, or be in ./quizcomp.constants.PROMPT_FILENAME.
        Both None and empty/white strings are ignored.

        Will raise an exception on an empty prompt.
        If this method does not raise an exception, the result will be placed in self.prompt.
        If the prompt is loaded from a file, self._prompt_path will be set with the absolute path.
        """

        text = self._get_prompt_text()
        self.prompt = self._validate_text_item(text, 'question prompt', check_feedback = False, allow_empty = False)

    def _get_prompt_text(self):
        # First check self.prompt.
        text = self.prompt
        if (text is None):
            text = ''

        text = text.strip()

        if (text != ''):
            return text

        # Next, check for prompt files.

        check_paths = [self._prompt_path, quizcomp.constants.PROMPT_FILENAME]
        for path in check_paths:
            if ((path is None) or (path.strip() == '')):
                continue

            if (not os.path.isabs(path)):
                path = os.path.join(self.base_dir, path)

            path = os.path.abspath(path)
            if (not os.path.exists(path)):
                continue

            logging.debug("Loading question prompt from '%s'.", path)
            self._prompt_path = path
            return quizcomp.util.dirent.read_file(path)

        raise quizcomp.common.QuestionValidationError(self, "Could not find any non-empty prompt.")

    def inherit_from_group(self, group):
        """
        Inherit attributes from a group.
        """

        self.points = group.points
        self.name = group.name

        if (group.custom_header is not None):
            self.custom_header = group.custom_header

        if (group.skip_numbering is not None):
            self.skip_numbering = group.skip_numbering

        self.shuffle_answers = (self.shuffle_answers and group.shuffle_answers)

        self.add_hints(group.hints)

    def add_hints(self, new_hints, override = False):
        for (key, value) in new_hints.items():
            if (override or (key not in self.hints)):
                self.hints[key] = value

    def collect_file_paths(self):
        paths = []

        for document in self._collect_documents([self.prompt, self.answers]):
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
        elif (isinstance(target, quizcomp.parser.public.ParsedText)):
            return [target.document]
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

        rng.shuffle(self.answers)

    # Override the class method JSONSerializer.from_dict() with a static method
    # so that we can select the correct child class.
    @staticmethod
    def from_dict(data, base_dir = None, ids = {}, **kwargs):
        if (base_dir is not None):
            data['base_dir'] = base_dir
        elif ('base_dir' not in data):
            data['base_dir'] = '.'

        if ('question_type' not in data):
            raise quizcomp.common.QuizValidationError("Question does not contain a 'question_type' field.", ids = ids)

        question_class = Question._fetch_question_class(data.get('question_type'), ids = ids, **kwargs)
        return quizcomp.util.serial._from_dict(question_class, data, ids = ids, **kwargs)

    @staticmethod
    def _fetch_question_class(question_type, ids = {}, **kwargs):
        if (not Question._imported_this_package):
            for _, name, is_package in pkgutil.iter_modules([THIS_DIR]):
                if (is_package):
                    continue

                module_name = BASE_MODULE_NAME + '.' + name
                importlib.import_module(module_name)

            _imported_this_package = True

        if (question_type not in Question._types):
            ids = ids.copy()
            ids['question_type'] = question_type

            raise quizcomp.common.QuizValidationError("Unknown question type.", ids = ids)

        return Question._types[question_type]

    def _validate_question_feedback(self):
        if (self.feedback is None):
            self.feedback = {}
            return

        if (isinstance(self.feedback, str)):
            self.feedback = {'general': self.feedback}

        self._check_type(self.feedback, dict, "'feedback'")

        allowed_keys = ['general', 'correct', 'incorrect']
        actual_keys = list(self.feedback.keys())

        bad_keys = list(sorted(set(actual_keys) - set(allowed_keys)))
        if (len(bad_keys) > 0):
            raise quizcomp.common.QuestionValidationError(self, "Unknown keys in feedback (%s). Allowed keys: '%s'." % (
                    str(bad_keys), str(allowed_keys)))

        new_feedback = {}
        for (key, value) in self.feedback.items():
            item = self._validate_feedback_item(value, "'%s' feedback value" % (key))
            if (item is not None):
                new_feedback[key] = item

        self.feedback = new_feedback

    def _validate_feedback_item(self, item, label):
        if ((item is None) or isinstance(item, quizcomp.parser.public.ParsedText)):
            # Nothing to do.
            return item

        self._check_type(item, str, label)

        item = item.strip()
        if (len(item) == 0):
            return None

        return quizcomp.parser.public.parse_text(item, base_dir = self.base_dir)

    def _validate_self_answer_list(self, min_correct = 0, max_correct = math.inf):
        self.answers = self._validate_answer_list(self.answers, self.base_dir,
                min_correct = min_correct, max_correct = max_correct)

    def _validate_answer_list(self, answers, base_dir, min_correct = 0, max_correct = math.inf):
        self._check_type(answers, list, "'answers'")

        if (len(answers) == 0):
            raise quizcomp.common.QuestionValidationError(self, f"No answers provided, at least one answer required.")

        num_correct = 0
        for answer in answers:
            if ('correct' not in answer):
                raise quizcomp.common.QuestionValidationError(self, f"Answer has no 'correct' field.")

            if ('text' not in answer):
                raise quizcomp.common.QuestionValidationError(self, f"Answer has no 'text' field.")

            if (answer['correct']):
                num_correct += 1

        if (num_correct < min_correct):
            raise quizcomp.common.QuestionValidationError(self, f"Did not find enough correct answers. Expected at least {min_correct}, found {num_correct}.")

        if (num_correct > max_correct):
            raise quizcomp.common.QuestionValidationError(self, f"Found too many correct answers. Expected at most {max_correct}, found {num_correct}.")

        new_answers = []
        for i in range(len(answers)):
            parsed_text = self._validate_text_item(answers[i], "'answers' values (element %d)" % (i))
            new_answer = quizcomp.question.common.ParsedTextChoice(parsed_text, answers[i]['correct'])
            new_answers.append(new_answer)

        return new_answers

    def _validate_text_answers(self):
        possible_answers = 'null/None, string, empty list, list of strings, or list of objects'

        if (self.answers is None):
            self.answers = ['']
        elif (isinstance(self.answers, str)):
            self.answers = [self.answers]

        if (not isinstance(self.answers, list)):
            raise quizcomp.common.QuestionValidationError(self, "'answers' value must be %s, found: '%s'." % (
                    possible_answers, str(self.answers)))

        if (len(self.answers) == 0):
            self.answers = ['']

        new_answers = []
        for i in range(len(self.answers)):
            new_answers.append(self._validate_text_item(self.answers[i], "'answers' values (element %d)" % (i)))

        self.answers = new_answers

    def _validate_text_item(self, item, label,
            check_feedback = True, allow_empty = True,
            strip = True, clean_whitespace = False):
        """
        Validate a portion of an answer/choice/field that is a parsed string.

        Allowed values are:
         - None (will be converted to an empty string).
         - Empty String (if allow_empty is True).
         - String
         - quizcomp.question.common.ParsedTextWithFeedback (will be passed back without any checks).
         - Dict with required key 'text' and optional key 'feedback'.

        If no exception is raised, a quizcomp.question.common.ParsedTextWithFeedback (child of quizcomp.parser.public.ParsedText)
        will be returned, even if there is no feedback.
        """

        if (isinstance(item, quizcomp.question.common.ParsedTextWithFeedback)):
            # Nothing to do if the item is already parsed.
            return item

        if (item is None):
            item = ''

        if (isinstance(item, str)):
            item = {'text': item}

        self._check_type(item, dict, label)

        if ('text' not in item):
            raise quizcomp.common.QuestionValidationError(self, "%s is missing a 'text' key." % (label))

        text = item['text']
        self._check_type(item['text'], str, "%s 'text' key" % (label))

        if (clean_whitespace):
            text = re.sub(r'\s+', ' ', text)

        if (strip):
            text = text.strip()

        if ((not allow_empty) and (text == '')):
            raise quizcomp.common.QuestionValidationError(self, "%s text is empty." % (label))

        feedback = None
        if (check_feedback):
            feedback = self._validate_feedback_item(item.get('feedback', None), label)

        return quizcomp.question.common.ParsedTextWithFeedback(quizcomp.parser.public.parse_text(text, base_dir = self.base_dir), feedback = feedback)

    def _validate_fimb_answers(self):
        self._check_type(self.answers, dict, "'answers' key")

        if (len(self.answers) == 0):
            raise quizcomp.common.QuestionValidationError(self, "Expected 'answers' dict to be non-empty.")

        for (key, values) in self.answers.items():
            # If this was already in the full FIMB format, then we need to pull out the values.
            if ((isinstance(values, dict)) and ('values' in values)):
                self.answers[key] = values['values']
            elif (not isinstance(values, list)):
                self.answers[key] = [values]

        new_answers = {}

        for (key, values) in self.answers.items():
            self._check_type(key, str, "key in 'answers' dict")

            if (len(values) == 0):
                raise quizcomp.common.QuestionValidationError(self, "Expected possible values to be non-empty.")

            new_values = []
            for i in range(len(values)):
                label = "answers key '%s' index %d" % (key, i)
                new_values.append(self._validate_text_item(values[i], label))

            new_answers[key] = {
                'key': quizcomp.parser.public.parse_text(key, base_dir = self.base_dir),
                'values': new_values,
            }

        self.answers = new_answers

        self._check_placeholders(self.answers.keys())

    def _check_type(self, value, expected_type, label):
        if (not isinstance(value, expected_type)):
            raise quizcomp.common.QuestionValidationError(self, f"{label} must be a {expected_type}, found '{value}' ({type(value)}).")

    def _check_placeholders(self, answer_placeholders):
        """
        Check placeholders from the answers against placeholders in the prompt.
        """

        answer_placeholders = set(list(answer_placeholders))
        document_placeholders = self.prompt.document.collect_placeholders()

        # Special case for FITB documents.
        if ((len(answer_placeholders) == 1) and (list(answer_placeholders)[0] == '')):
            if (len(document_placeholders) != 0):
                output_answer_placeholders = list(sorted(answer_placeholders))
                raise quizcomp.common.QuestionValidationError(self, "Found placeholders (%s) in the question prompt when none were expected." % (output_answer_placeholders))

            return

        if (answer_placeholders != document_placeholders):
            output_answer_placeholders = list(sorted(answer_placeholders))
            output_document_placeholders = list(sorted(document_placeholders))

            raise quizcomp.common.QuestionValidationError(self, "Mismatch between the placeholders found in the question prompt (%s) and answers config (%s)." % (output_document_placeholders, output_answer_placeholders))
