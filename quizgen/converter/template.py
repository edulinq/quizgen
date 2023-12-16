"""
Convert a quiz using template files.
"""

import math
import os
import random
import re

import quizgen.constants
import quizgen.converter.base
import quizgen.util.file

# TEST -- Question TOC
# TEST -- Answer Shuffling
# TEST -- Generate Seed as part of footer.

# Template variabes.
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
TEMPLATE_FILENAME_QUESTION = 'question.template'
TEMPLATE_FILENAME_QUIZ = 'quiz.template'
TEMPLATE_QUESTION_TYPES_DIR = 'question-types'

DATE_FORMAT = '%B %d, %Y'

class TemplateConverter(quizgen.converter.base.QuizConverter):
    def __init__(self, format, template_dir, **kwargs):
        super().__init__(**kwargs)

        if (not os.path.isdir(template_dir)):
            raise ValueError("Provided template dir ('%s') does not exist or is not a dir." % (
                template_dir))

        self.format = format
        self.template_dir = template_dir

        # Methods to generate answers.
        # Signatuire: func(self, base_template (for an answer of this type), answers)
        self.answer_functions = {
            quizgen.constants.QUESTION_TYPE_MCQ: 'create_answers_list',
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

        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_BODY)
        path = os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename)
        if (not os.path.isfile(path)):
            raise ValueError("Question template does not exist or is not a file: '%s'." % (path))

        template = quizgen.util.file.read(path)

        prompt_document = self.check_variable(question, 'prompt_document', label = 'Question')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_PROMPT,
                question.prompt_document.to_format(self.format))

        answers = self.check_variable(question, 'answers', label = 'Question')
        answers_text = self.create_answers(question_type, answers)
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ANSWERS, answers_text)

        return template

    def create_answers(self, question_type, answers):
        filename = "%s_%s" % (question_type, TEMPLATE_FILENAME_ANSWER)
        base_template = quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_QUESTION_TYPES_DIR, filename))

        if (question_type not in self.answer_functions):
            raise ValueError("Cannot create question answers, unsupported question type: '%s'." % (question_type))

        method = self.check_variable(self, self.answer_functions[question_type], label = 'Converter')
        return method(base_template, answers)

    def create_answers_list(self, base_template, answers):
        answers_text = []

        for answer in answers:
            template = base_template

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_TEXT,
                    answer['document'].to_format(self.format))

            answers_text.append(template)

        return "\n\n".join(answers_text)

    def create_answers_noop(self, base_template, answers):
        return base_template

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
        template = self.fill_variable(template, TEMPLATE_VAR_VERSION, "Version: " + version)

        num_questions = quiz.num_questions()
        template = self.fill_variable(template, TEMPLATE_VAR_NUM_QUESTIONS, str(num_questions))
        template = self.fill_variable(template, TEMPLATE_VAR_NUM_QUESTIONS_DIV_EIGHT_CEIL, str(math.ceil(num_questions / 8)))

        return template

    def fill_variable(self, template, variable, value):
        return template.replace(variable, value)

    def check_variable(self, source, name, label = "Object"):
        value = getattr(source, name, '')
        if ((value is None) or (value == '')):
            raise ValueError("%s is missing key value: '%s'." % (label, name))

        return value
