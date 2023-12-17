"""
Convert a quiz using template files.
"""

import math
import os
import string
import random
import re

import quizgen.constants
import quizgen.converter.base
import quizgen.util.file

# TEST -- Answer Shuffling
# TEST -- Generate Seed as part of footer.

# Template variabes.
TEMPLATE_VAR_ANSWER_CHOICE_TEXT = '{{{ANSWER_CHOICE_TEXT}}}'
TEMPLATE_VAR_ANSWER_CHOICES = '{{{ANSWER_CHOICES}}}'
TEMPLATE_VAR_ANSWER_LEFT = '{{{ANSWER_LEFT}}}'
TEMPLATE_VAR_ANSWER_LEFT_ID = '{{{ANSWER_LEFT_ID}}}'
TEMPLATE_VAR_ANSWER_RIGHT = '{{{ANSWER_RIGHT}}}'
TEMPLATE_VAR_ANSWER_RIGHT_ID = '{{{ANSWER_RIGHT_ID}}}'
TEMPLATE_VAR_ANSWER_TEXT = '{{{ANSWER_TEXT}}}'
TEMPLATE_VAR_COURSE_TITLE = '{{{COURSE_TITLE}}}'
TEMPLATE_VAR_DATE = '{{{DATE}}}'
TEMPLATE_VAR_DESCRIPTION = '{{{DESCRIPTION}}}'
TEMPLATE_VAR_GROUPS = '{{{GROUPS}}}'
TEMPLATE_VAR_NUM_QUESTIONS = '{{{NUM_QUESTIONS}}}'
TEMPLATE_VAR_NUM_QUESTIONS_DIV_EIGHT_CEIL = '{{{NUM_QUESTIONS_DIV_EIGHT_CEIL}}}'
TEMPLATE_VAR_QUESTION_ANSWERS = '{{{QUESTION_ANSWERS}}}'
TEMPLATE_VAR_QUESTION_BODY = '{{{QUESTION_BODY}}}'
TEMPLATE_VAR_QUESTION_NAME = '{{{QUESTION_NAME}}}'
TEMPLATE_VAR_QUESTION_NUMBER = '{{{QUESTION_NUMBER}}}'
TEMPLATE_VAR_QUESTION_POINTS = '{{{QUESTION_POINTS}}}'
TEMPLATE_VAR_QUESTION_PROMPT = '{{{QUESTION_PROMPT}}}'
TEMPLATE_VAR_TERM_TITLE = '{{{TERM_TITLE}}}'
TEMPLATE_VAR_TITLE = '{{{TITLE}}}'
TEMPLATE_VAR_VERSION = '{{{VERSION}}}'

# Template filenames.
TEMPLATE_FILENAME_ANSWER = 'answer.template'
TEMPLATE_FILENAME_BODY = 'body.template'
TEMPLATE_FILENAME_CHOICE = 'choice.template'
TEMPLATE_FILENAME_QUESTION = 'question.template'
TEMPLATE_FILENAME_QUIZ = 'quiz.template'
TEMPLATE_QUESTION_TYPES_DIR = 'question-types'

DATE_FORMAT = '%B %d, %Y'

RIGHT_IDS = string.ascii_uppercase
LEFT_IDS = [str(i + 1) for i in range(len(RIGHT_IDS))]

class TemplateConverter(quizgen.converter.base.QuizConverter):
    def __init__(self, format, template_dir, **kwargs):
        super().__init__(**kwargs)

        if (not os.path.isdir(template_dir)):
            raise ValueError("Provided template dir ('%s') does not exist or is not a dir." % (
                template_dir))

        self.format = format
        self.template_dir = template_dir

        # Methods to generate answers.
        # Signatuire: func(self, base_template (for an answer of this type), question)
        self.answer_functions = {
            quizgen.constants.QUESTION_TYPE_ESSAY: 'create_answers_noop',
            quizgen.constants.QUESTION_TYPE_FIMB: 'create_answers_fimb',
            quizgen.constants.QUESTION_TYPE_MATCHING: 'create_answers_matching',
            quizgen.constants.QUESTION_TYPE_MA: 'create_answers_list',
            quizgen.constants.QUESTION_TYPE_MCQ: 'create_answers_list',
            quizgen.constants.QUESTION_TYPE_MDD: 'create_answers_mdd',
            quizgen.constants.QUESTION_TYPE_NUMERICAL: 'create_answers_noop',
            quizgen.constants.QUESTION_TYPE_SA: 'create_answers_noop',
            quizgen.constants.QUESTION_TYPE_TEXT_ONLY: 'create_answers_noop',
            quizgen.constants.QUESTION_TYPE_TF: 'create_answers_noop',
        }

    def convert_quiz(self, quiz, **kwargs):
        template = quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_FILENAME_QUIZ))

        template = self.fill_metadata(template, quiz);

        groups = self.create_groups(quiz)
        template = self.fill_variable(template, TEMPLATE_VAR_GROUPS, groups)

        match = re.search(r'\{\{\{\w+\}\}\}', template)
        if (match is not None):
            raise ValueError("Found unresolved template variable: '%s'." % (match.group(0)))

        return template

    def create_groups(self, quiz):
        groups = []

        for i in range(len(quiz.groups)):
            group = quiz.groups[i]

            # TEST - Note the question chosen.
            question = random.choice(group.questions)

            groups.append(self.create_question(i + 1, group, question))

        return "\n\n".join(groups)

    def create_question(self, number, group, question):
        template = quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_FILENAME_QUESTION))

        name = self.check_variable(group, 'name', label = 'Group')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_NAME, group.name)

        points = self.check_variable(group, 'points', label = 'Group')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_POINTS, str(group.points))

        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_NUMBER, str(number))

        body = self.create_question_body(question)
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_BODY, body)

        return template

    def create_question_body(self, question):
        question_type = self.check_variable(question, 'question_type', label = 'Question')
        if (question_type not in self.answer_functions):
            raise ValueError("Unsupported question type: '%s'." % (question_type))

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_BODY)
        path = os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename)
        if (not os.path.isfile(path)):
            raise ValueError("Question template does not exist or is not a file: '%s'." % (path))

        template = quizgen.util.file.read(path)

        prompt_document = self.check_variable(question, 'prompt_document', label = 'Question')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_PROMPT,
                question.prompt_document.to_format(self.format))

        answers = self.check_variable(question, 'answers', label = 'Question')
        answers_text = self.create_answers(question, answers)
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ANSWERS, answers_text)

        return template

    def create_answers(self, question, answers):
        question_type = self.check_variable(question, 'question_type', label = 'Question')

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_ANSWER)
        base_template = quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename))

        if (question_type not in self.answer_functions):
            raise ValueError("Cannot create question answers, unsupported question type: '%s'." % (question_type))

        method = self.check_variable(self, self.answer_functions[question_type], label = 'Converter')
        return method(base_template, question)

    def create_answers_list(self, base_template, question):
        answers_text = []

        for answer_document in question.answers_documents:
            template = base_template

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_TEXT,
                    answer_document.to_format(self.format))

            answers_text.append(template)

        return "\n\n".join(answers_text)

    def create_answers_noop(self, base_template, question):
        return base_template

    def create_answers_mdd(self, base_template, question):
        answers_text = []

        for (key, values) in question.answers.items():
            template = base_template
            key_document = question.answers_documents[key]['key']

            choices_text = self.create_choices_mdd(question, key)

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_TEXT,
                    key_document.to_format(self.format))

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_CHOICES, choices_text)

            answers_text.append(template)

        return "\n\n".join(answers_text)

    def create_choices_mdd(self, question, key):
        # TODO - Shuffle

        question_type = self.check_variable(question, 'question_type', label = 'Question')

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_CHOICE)
        base_template = quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename))

        choices_text = []

        for i in range(len(question.answers[key])):
            template = base_template
            choice_document = question.answers_documents[key]['values'][i]

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_CHOICE_TEXT,
                    choice_document.to_format(self.format))

            choices_text.append(template)

        return "\n\n".join(choices_text)

    def create_answers_fimb(self, base_template, question):
        # TODO - Shuffle

        answers_text = []

        for key in question.answers:
            template = base_template
            key_document = question.answers_documents[key]['key']

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_TEXT,
                    key_document.to_format(self.format))

            answers_text.append(template)

        return "\n\n".join(answers_text)

    def create_answers_matching(self, base_template, question):
        left_ids = self.get_left_ids()
        right_ids = self.get_right_ids()

        lefts = []
        rights = []

        for (left, right) in question.answers_documents['matches']:
            lefts.append(left.to_format(self.format))
            rights.append(right.to_format(self.format))

        for right in question.answers_documents['distractors']:
            rights.append(right.to_format(self.format))

        if (len(lefts) > len(left_ids)):
            raise ValueError("Too many matching values. Max allowed: '%d'." % (len(left_ids)))

        if (len(rights) > len(right_ids)):
            raise ValueError("Too many distractors. Max allowed: '%d'." % (len(right_ids)))

        # TODO -- Shuffle

        answers_text = []
        for i in range(max(len(lefts), len(rights))):
            template = base_template

            left = ''
            left_id = ''
            if (i < len(lefts)):
                left = lefts[i]
                left_id = left_ids[i]

            right = ''
            right_id = ''
            if (i < len(rights)):
                right = rights[i]
                right_id = right_ids[i]

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_LEFT, left);
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_LEFT_ID, left_id);

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_RIGHT, right);
            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_RIGHT_ID, right_id);

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

        # TEST - Variant Information
        version = self.check_variable(quiz, 'version', label = 'Quiz')
        template = self.fill_variable(template, TEMPLATE_VAR_VERSION, version)

        num_questions = quiz.num_questions()
        template = self.fill_variable(template, TEMPLATE_VAR_NUM_QUESTIONS, str(num_questions))
        template = self.fill_variable(template, TEMPLATE_VAR_NUM_QUESTIONS_DIV_EIGHT_CEIL, str(math.ceil(num_questions / 8)))

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
