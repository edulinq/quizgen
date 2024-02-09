import datetime
import json
import logging
import os
import random

import json5

import quizgen.common
import quizgen.group
import quizgen.parser
import quizgen.uploader.canvas
import quizgen.util.file
import quizgen.util.git

class Quiz(object):
    def __init__(self,
            title = '',
            course_title = '', term_title = '',
            description = '', date = '',
            time_limit_mins = None, shuffle_answers = True,
            groups = [],
            base_dir = '.',
            version = None,
            canvas = {},
            **kwargs):
        self.title = title
        self.course_title = course_title
        self.term_title = term_title
        self.date = date

        self.description = description
        self.description_document = None

        self.time_limit_mins = time_limit_mins
        self.shuffle_answers = shuffle_answers

        self.groups = groups

        self.version = version
        self.base_dir = base_dir

        self.canvas = canvas.copy()

        try:
            self.validate(kwargs)
        except Exception as ex:
            raise quizgen.common.QuizValidationError("Error while validating quiz '%s'." % self.title) from ex

    def validate(self, kwargs):
        if ((self.title is None) or (self.title == "")):
            raise quizgen.common.QuizValidationError("Title cannot be empty.")

        if ((self.description is None) or (self.description == "")):
            raise quizgen.common.QuizValidationError("Description cannot be empty.")
        self.description_document = quizgen.parser.parse_text(self.description,
                base_dir = self.base_dir)

        if (self.version is None):
            self.version = quizgen.util.git.get_version(self.base_dir, throw = False)
            if (self.version == quizgen.util.git.UNKNOWN_VERSION):
                logging.warning("Could not get a version for the quiz (is it in a git repo?).")

        self.canvas = quizgen.uploader.canvas.validate_options(self.canvas)

        self._validate_time_limit()

        if (self.date == ''):
            self.date = datetime.date.today()
        else:
            self.date = datetime.date.fromisoformat(self.date)

        for key in kwargs:
            logging.warning("Unknown quiz option: '%s'." % (key))

    def _validate_time_limit(self):
        if (self.time_limit_mins is None):
            return

        if (not isinstance(self.time_limit_mins, (str, int))):
            raise quizgen.common.QuizValidationError("Time limit must be a positive int, found '%s'." % (str(self.time_limit_mins)))

        try:
            self.time_limit_mins = int(self.time_limit_mins)
        except:
            raise quizgen.common.QuizValidationError("Time limit must be a positive int, found '%s'." % (str(self.time_limit_mins)))

        if (self.time_limit_mins < 0):
            raise quizgen.common.QuizValidationError("Time limit must be a positive int, found '%s'." % (str(self.time_limit_mins)))

        if (self.time_limit_mins == 0):
            self.time_limit_mins = None

    def to_dict(self, include_docs = True, flatten_groups = False):
        value = self.__dict__.copy()

        if ('date' in value):
            value['date'] = value['date'].isoformat()

        value['groups'] = [group.to_dict(include_docs = include_docs) for group in self.groups]

        if (include_docs):
            value['description_document'] = self.description_document.to_pod()
        else:
            del value['description_document']

        return value

    @staticmethod
    def from_path(path, flatten_groups = False):
        path = os.path.abspath(path)

        with open(path, 'r') as file:
            quiz_info = json5.load(file)

        # Check for a description file.
        description_filename = os.path.splitext(os.path.basename(path))[0]
        description_path = os.path.join(os.path.dirname(path), description_filename + '.md')
        if (os.path.exists(description_path)):
            quiz_info['description'] = quizgen.util.file.read(description_path)
            logging.debug("Loading quiz description from '%s'.", description_path)

        base_dir = os.path.dirname(path)

        return Quiz.from_dict(quiz_info, base_dir, flatten_groups = flatten_groups)

    @staticmethod
    def from_dict(quiz_info, base_dir = None, flatten_groups = False):
        groups = [quizgen.group.Group.from_dict(group_info, base_dir) for group_info in quiz_info.get('groups', [])]

        if (flatten_groups):
            new_groups = []

            for old_group in groups:
                for i in range(len(old_group.questions)):
                    info = {
                        'name': old_group.name,
                        'pick_count': 1,
                        'points': old_group.points,
                        'questions': [old_group.questions[i]],
                    }

                    new_groups.append(quizgen.group.Group(**info))

            groups = new_groups

        quiz_info['groups'] = groups

        if (base_dir is not None):
            quiz_info['base_dir'] = base_dir
        elif ('base_dir' not in quiz_info):
            quiz_info['base_dir'] = '.'

        return Quiz(**quiz_info)

    def to_json(self, indent = 4, include_docs = True):
        return json.dumps(self.to_dict(include_docs = include_docs), indent = indent)

    def num_questions(self):
        count = 0

        for group in self.groups:
            count += group.pick_count

        return count

    def create_variant(self, identifier = None, seed = None, all_questions = False):
        if (seed is None):
            seed = random.randint(0, 2**64)

        logging.debug("Creating variant with seed %s.", str(seed))
        rng = random.Random(seed)

        questions = []
        for group in self.groups:
            new_questions = None

            if (all_questions):
                new_questions = group.copy_questions()
            else:
                new_questions = group.choose_questions(rng)

            if (len(new_questions) > 1):
                for i in range(len(new_questions)):
                    new_questions[i].base_name = "%s - %d" % (group.name, i + 1)

            questions += new_questions

        if (self.shuffle_answers):
            for question in questions:
                question.shuffle(rng)

        title = self.title
        version = self.version

        if (identifier is not None):
            title = "%s - %s" % (title, identifier)
            version = "%s, Variant: %s" % (version, identifier)

        return quizgen.variant.Variant(
            title = title,
            course_title = self.course_title, term_title = self.term_title,
            description = self.description, description_document = self.description_document,
            date = self.date,
            questions = questions,
            version = version, seed = seed)
