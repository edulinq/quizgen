"""
Convert a quiz using template files.
"""

import math
import os
import string
import random
import re

import quizgen.variant
import quizgen.constants
import quizgen.util.file

# Template variabes.
TEMPLATE_VAR_ANSWER_CHOICE_INDEX = '{{{ANSWER_CHOICE_INDEX}}}'
TEMPLATE_VAR_ANSWER_CHOICE_TEXT = '{{{ANSWER_CHOICE_TEXT}}}'
TEMPLATE_VAR_ANSWER_CHOICES = '{{{ANSWER_CHOICES}}}'
TEMPLATE_VAR_ANSWER_ID = '{{{ANSWER_ID}}}'
TEMPLATE_VAR_ANSWER_LEFT = '{{{ANSWER_LEFT}}}'
TEMPLATE_VAR_ANSWER_LEFT_ID = '{{{ANSWER_LEFT_ID}}}'
TEMPLATE_VAR_ANSWER_RIGHT = '{{{ANSWER_RIGHT}}}'
TEMPLATE_VAR_ANSWER_RIGHT_ID = '{{{ANSWER_RIGHT_ID}}}'
TEMPLATE_VAR_ANSWER_TEXT = '{{{ANSWER_TEXT}}}'
TEMPLATE_VAR_ANSWER_SOLUTION = '{{{ANSWER_SOLUTION}}}'
TEMPLATE_VAR_ANSWER_KEY = '{{{ANSWER_KEY}}}'
TEMPLATE_VAR_COURSE_TITLE = '{{{COURSE_TITLE}}}'
TEMPLATE_VAR_DATE = '{{{DATE}}}'
TEMPLATE_VAR_DESCRIPTION = '{{{DESCRIPTION}}}'
TEMPLATE_VAR_NUM_QUESTIONS = '{{{NUM_QUESTIONS}}}'
TEMPLATE_VAR_NUM_QUESTIONS_DIV_EIGHT_CEIL = '{{{NUM_QUESTIONS_DIV_EIGHT_CEIL}}}'
TEMPLATE_VAR_QUESTION_ANSWERS = '{{{QUESTION_ANSWERS}}}'
TEMPLATE_VAR_QUESTION_BODY = '{{{QUESTION_BODY}}}'
TEMPLATE_VAR_QUESTION_ID = '{{{QUESTION_ID}}}'
TEMPLATE_VAR_QUESTION_NAME = '{{{QUESTION_NAME}}}'
TEMPLATE_VAR_QUESTION_NUMBER = '{{{QUESTION_NUMBER}}}'
TEMPLATE_VAR_QUESTION_POINTS = '{{{QUESTION_POINTS}}}'
TEMPLATE_VAR_QUESTION_PROMPT = '{{{QUESTION_PROMPT}}}'
TEMPLATE_VAR_QUESTIONS = '{{{QUESTIONS}}}'
TEMPLATE_VAR_TERM_TITLE = '{{{TERM_TITLE}}}'
TEMPLATE_VAR_TITLE = '{{{TITLE}}}'
TEMPLATE_VAR_VERSION = '{{{VERSION}}}'

# Template filenames.
TEMPLATE_FILENAME_ANSWER = 'answer.template'
TEMPLATE_FILENAME_BODY = 'body.template'
TEMPLATE_FILENAME_CHOICE = 'choice.template'
TEMPLATE_FILENAME_KEY = 'key.template'
TEMPLATE_FILENAME_QUESTION = 'question.template'
TEMPLATE_FILENAME_QUESTION_SEPARATOR = 'question-separator.template'
TEMPLATE_FILENAME_QUIZ = 'quiz.template'
TEMPLATE_QUESTION_TYPES_DIR = 'question-types'

ANSWER_KEY_TEXT = 'Answer Key'

DATE_FORMAT = '%B %d, %Y'

RIGHT_IDS = string.ascii_uppercase
LEFT_IDS = [str(i + 1) for i in range(len(RIGHT_IDS))]

class TemplateConverter(object):
    def __init__(self, format, template_dir, answer_key = False, **kwargs):
        super().__init__()

        if (not os.path.isdir(template_dir)):
            raise ValueError("Provided template dir ('%s') does not exist or is not a dir." % (
                template_dir))

        self.format = format
        self.template_dir = template_dir
        self.answer_key = answer_key

        # Methods to generate answers.
        # Signatuire: func(self, base_template (for an answer of this type), key_template (if exists) question_number, question)
        self.answer_functions = {
            quizgen.constants.QUESTION_TYPE_ESSAY: 'create_answers_textbox',
            quizgen.constants.QUESTION_TYPE_FIMB: 'create_answers_fimb',
            quizgen.constants.QUESTION_TYPE_FITB: 'create_answers_fitb',
            quizgen.constants.QUESTION_TYPE_MATCHING: 'create_answers_matching',
            quizgen.constants.QUESTION_TYPE_MA: 'create_answers_list',
            quizgen.constants.QUESTION_TYPE_MCQ: 'create_answers_list',
            quizgen.constants.QUESTION_TYPE_MDD: 'create_answers_mdd',
            quizgen.constants.QUESTION_TYPE_NUMERICAL: 'create_answers_numerical',
            quizgen.constants.QUESTION_TYPE_SA: 'create_answers_textbox',
            quizgen.constants.QUESTION_TYPE_TEXT_ONLY: 'create_answers_textbox',
            quizgen.constants.QUESTION_TYPE_TF: 'create_answers_list',
        }

    def convert_quiz(self, quiz, **kwargs):
        if (not isinstance(quiz, quizgen.variant.Variant)):
            raise ValueError("Template quiz converter requires a quizgen.quiz.Variant type, found %s." % (type(quiz)))

        template = quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_FILENAME_QUIZ), strip = False)

        template = self.fill_metadata(template, quiz)

        questions = self.create_questions(quiz)
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTIONS, questions)

        match = re.search(r'\{\{\{\w+\}\}\}', template)
        if (match is not None):
            raise ValueError("Found unresolved template variable: '%s'." % (match.group(0)))

        return template

    def clean_solution_content(self, document):
        """
        An opportunity for children to clean the text of a solution before it is entered into a key.
        For example, tex solutions are hacky and cannot use certain functions.
        """

        return document.to_format(self.format)

    def create_questions(self, quiz):
        questions = []

        for i in range(len(quiz.questions)):
            if (i != 0):
                questions.append(self.create_question_separator())

            questions.append(self.create_question(i + 1, quiz.questions[i]))

        return "\n\n".join(questions)

    def create_question(self, number, question):
        template = quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_FILENAME_QUESTION), strip = False)

        name = self.check_variable(question, 'base_name', label = 'Question')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_NAME, question.base_name)

        points = self.check_variable(question, 'points', label = 'Question')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_POINTS, str(question.points))

        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_NUMBER, str(number))

        body = self.create_question_body(number, question)
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_BODY, body)

        return template

    def create_question_separator(self):
        return quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_FILENAME_QUESTION_SEPARATOR), strip = False)

    def create_question_body(self, question_number, question):
        question_type = self.check_variable(question, 'question_type', label = 'Question')
        if (question_type not in self.answer_functions):
            raise ValueError("Unsupported question type: '%s'." % (question_type))

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_BODY)
        path = os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename)
        if (not os.path.isfile(path)):
            raise ValueError("Question template does not exist or is not a file: '%s'." % (path))

        template = quizgen.util.file.read(path, strip = False)

        prompt_document = self.check_variable(question, 'prompt_document', label = 'Question')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_PROMPT,
                question.prompt_document.to_format(self.format))

        answers = self.check_variable(question, 'answers', label = 'Question')
        answers_text = self.create_answers(question_number, question, answers)
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ANSWERS, answers_text)

        return template

    def create_answers(self, question_number, question, answers):
        question_type = self.check_variable(question, 'question_type', label = 'Question')

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_ANSWER)
        path = os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename)
        base_template = quizgen.util.file.read(path, strip = False)

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_KEY)
        path = os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename)
        key_template = quizgen.util.file.read_if_exists(path, strip = False)

        if (question_type not in self.answer_functions):
            raise ValueError("Cannot create question answers, unsupported question type: '%s'." % (question_type))

        method = self.check_variable(self, self.answer_functions[question_type], label = 'Converter')
        return method(base_template, key_template, question_number, question)

    def create_answers_list(self, base_template, key_template, question_number, question):
        answers_text = []

        for i in range(len(question.answers_documents)):
            if (self.answer_key and question.answers[i]['correct'] and (key_template is not None)):
                template = key_template
            else:
                template = base_template

            answer_document = question.answers_documents[i]
            answer_id = "%d.%d" % (question_number, i)

            template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ID, str(question_number))
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_ID, answer_id)

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_TEXT,
                    answer_document.to_format(self.format))

            answers_text.append(template)

        return "\n".join(answers_text)

    def create_answers_numerical(self, base_template, key_template, question_number, question):
        content = None

        answer = question.answers[0]
        if (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_EXACT):
            content = "%f ± %f" % (answer['value'], answer['margin'])
        elif (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_PRECISION):
            content = "[%f, %f]" % (answer['min'], answer['max'])
        elif (answer['type'] == quizgen.constants.NUMERICAL_ANSWER_TYPE_RANGE):
            content = "%f (precision: %f)" % (answer['value'], answer['precision'])

        return self.create_answers_textbox(base_template, key_template, question_number, question, answer_content = content)

    def create_answers_fitb(self, base_template, key_template, question_number, question):
        document = question.answers_documents['']['values'][0]
        return self.create_answers_textbox(base_template, key_template, question_number, question, answer_document = document)

    def create_answers_textbox(self, base_template, key_template, question_number, question,
            answer_document = None, answer_content = None):
        if (self.answer_key and (key_template is not None)):
            template = key_template
        else:
            template = base_template

        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ID, str(question_number))
        template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_ID, str(question_number))

        if (answer_document is not None):
            answer_content = self.clean_solution_content(answer_document)

        if (answer_content is not None):
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_SOLUTION, answer_content)

        return template

    def create_answers_mdd(self, base_template, key_template, question_number, question):
        answers_text = []
        i = 0

        for (key, values) in question.answers.items():
            template = base_template
            key_document = question.answers_documents[key]['key']
            answer_id = "%d.%d" % (question_number, i)

            choices_text = self.create_choices_mdd(question_number, question, answer_id, key)

            template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ID, str(question_number))
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_ID, answer_id)

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_TEXT,
                    key_document.to_format(self.format))

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_CHOICES, choices_text)

            answers_text.append(template)
            i += 1

        return "\n\n".join(answers_text)

    def create_choices_mdd(self, question_number, question, answer_id, key):
        question_type = self.check_variable(question, 'question_type', label = 'Question')

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_CHOICE)
        path = os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename)
        base_template = quizgen.util.file.read(path, strip = False)

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_KEY)
        path = os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename)
        key_template = quizgen.util.file.read_if_exists(path, strip = False)

        choices_text = []

        for i in range(len(question.answers[key])):
            if (self.answer_key and question.answers[key][i]['correct'] and (key_template is not None)):
                template = key_template
            else:
                template = base_template

            choice_document = question.answers_documents[key]['values'][i]

            template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ID, str(question_number))
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_ID, answer_id)

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_CHOICE_INDEX, str(i))

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_CHOICE_TEXT,
                    choice_document.to_format(self.format))

            choices_text.append(template)

        return "\n".join(choices_text)

    def create_answers_fimb(self, base_template, key_template, question_number, question):
        answers_text = []
        i = 0

        for key in question.answers:
            if (self.answer_key and (key_template is not None)):
                template = key_template
            else:
                template = base_template

            key_document = question.answers_documents[key]['key']
            answer_id = "%d.%d" % (question_number, i)

            solution_document = question.answers_documents[key]['values'][0]

            template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ID, str(question_number))
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_ID, answer_id)

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_SOLUTION, self.clean_solution_content(solution_document))

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_TEXT,
                    key_document.to_format(self.format))

            answers_text.append(template)
            i += 1

        return "\n\n".join(answers_text)

    def create_answers_matching(self, base_template, key_template, question_number, question):
        lefts = []
        rights = []

        # {left_index: right_index, ...}
        matches = {}

        for (left, right) in question.answers_documents['matches']:
            matches[len(lefts)] = len(rights)

            lefts.append(left.to_format(self.format))
            rights.append(right.to_format(self.format))

        for right in question.answers_documents['distractors']:
            rights.append(right.to_format(self.format))

        if (question.answers.get('shuffle', False)):
            seed = question.answers.get('shuffle_seed', None)
            rng = random.Random(seed)

            # Shuffle the left and right options while maintining the match mapping.
            left_indexes = list(range(len(lefts)))
            right_indexes = list(range(len(rights)))

            rng.shuffle(left_indexes)
            rng.shuffle(right_indexes)

            new_lefts = [lefts[index] for index in left_indexes]
            lefts = new_lefts

            new_rights = [rights[index] for index in right_indexes]
            rights = new_rights

            new_matches = {left_indexes.index(old_left_index): right_indexes.index(old_right_index) for (old_left_index, old_right_index) in matches.items()}
            matches = new_matches

        return self.create_choices_matching(base_template, key_template, question_number, lefts, rights, matches)

    def create_choices_matching(self, base_template, key_template, question_number, lefts, rights, matches):
        left_ids = self.get_left_ids()
        right_ids = self.get_right_ids()

        if (len(lefts) > len(left_ids)):
            raise ValueError("Too many matching values. Max allowed: '%d'." % (len(left_ids)))

        if (len(rights) > len(right_ids)):
            raise ValueError("Too many distractors. Max allowed: '%d'." % (len(right_ids)))

        answers_text = []
        for i in range(max(len(lefts), len(rights))):
            template = base_template
            answer_id = "%d.%d" % (question_number, i)

            left = ''
            left_id = ''
            if (i < len(lefts)):
                left = lefts[i]
                left_id = left_ids[i]

                solution = ''
                if (self.answer_key and (key_template is not None)):
                    template = key_template
                    solution = right_ids[matches[i]]

            right = ''
            right_id = ''
            if (i < len(rights)):
                right = rights[i]
                right_id = right_ids[i]

            template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ID, str(question_number))
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_ID, answer_id)

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_LEFT, left)
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_LEFT_ID, left_id)

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_RIGHT, right)
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_RIGHT_ID, right_id)

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_SOLUTION, right)

            answers_text.append(template)

        return "\n".join(answers_text)

    def fill_metadata(self, template, quiz):
        title = self.check_variable(quiz, 'title', label = 'Quiz')
        template = self.fill_variable(template, TEMPLATE_VAR_TITLE, title)

        course_title = self.check_variable(quiz, 'course_title', label = 'Quiz')
        template = self.fill_variable(template, TEMPLATE_VAR_COURSE_TITLE, course_title)

        term_title = self.check_variable(quiz, 'term_title', label = 'Quiz')
        template = self.fill_variable(template, TEMPLATE_VAR_TERM_TITLE, term_title)

        date = self.check_variable(quiz, 'date', label = 'Quiz')
        template = self.fill_variable(template, TEMPLATE_VAR_DATE, date.strftime(DATE_FORMAT))

        template = self.fill_variable(template, TEMPLATE_VAR_DESCRIPTION,
                quiz.description_document.to_format(self.format))

        version = self.check_variable(quiz, 'version', label = 'Quiz')
        template = self.fill_variable(template, TEMPLATE_VAR_VERSION, version)

        num_questions = quiz.num_questions()
        template = self.fill_variable(template, TEMPLATE_VAR_NUM_QUESTIONS, str(num_questions))
        template = self.fill_variable(template, TEMPLATE_VAR_NUM_QUESTIONS_DIV_EIGHT_CEIL, str(math.ceil(num_questions / 8)))

        if (self.answer_key):
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_KEY, ANSWER_KEY_TEXT)
        else:
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_KEY, '')

        return template

    def get_left_ids(self):
        return LEFT_IDS

    def get_right_ids(self):
        return RIGHT_IDS

    def fill_variable(self, template, variable, value):
        return template.replace(variable, value)

    def check_variable(self, source, name, label = "Object"):
        value = getattr(source, name, '')
        if ((value is None) or (value == '')):
            raise ValueError("%s is missing key value: '%s'." % (label, name))

        return value
