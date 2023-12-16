"""
Convert a quiz using template files.
"""

import os
import random

import quizgen.constants
import quizgen.converter.base
import quizgen.util.file

# TEST -- Question TOC

# Template variabes.
TEMPLATE_VAR_ANSWER_TEXT = '{{{ANSWER_TEXT}}}'
TEMPLATE_VAR_COURSE_TITLE = '{{{COURSE_TITLE}}}'
TEMPLATE_VAR_DATE = '{{{DATE}}}'
TEMPLATE_VAR_DESCRIPTION = '{{{DESCRIPTION}}}'
TEMPLATE_VAR_GROUPS = '{{{GROUPS}}}'
TEMPLATE_VAR_HEADER = '{{{HEADER}}}'
TEMPLATE_VAR_QUESTION_ANSWERS = '{{{QUESTION_ANSWERS}}}'
TEMPLATE_VAR_QUESTION_BODY = '{{{QUESTION_BODY}}}'
TEMPLATE_VAR_QUESTION_NAME = '{{{QUESTION_NAME}}}'
TEMPLATE_VAR_QUESTION_NUMBER = '{{{QUESTION_NUMBER}}}'
TEMPLATE_VAR_QUESTION_POINTS = '{{{QUESTION_POINTS}}}'
TEMPLATE_VAR_QUESTION_PROMPT = '{{{QUESTION_PROMPT}}}'
TEMPLATE_VAR_TERM_TITLE = '{{{TERM_TITLE}}}'
TEMPLATE_VAR_TITLE = '{{{TITLE}}}'

# Template filenames.
TEMPLATE_FILENAME_ANSWER = 'answer.template'
TEMPLATE_FILENAME_QUESTION = 'question.template'
TEMPLATE_FILENAME_QUIZ = 'quiz.template'

DATE_FORMAT = '%B %d, %Y'

class TemplateConverter(quizgen.converter.base.QuizConverter):
    def __init__(self, format, template_dir, **kwargs):
        super().__init__(**kwargs)

        if (not os.path.isdir(template_dir)):
            raise ValueError("Provided template dir ('%s') does not exist or is not a dir." % (
                template_dir))

        self.format = format
        self.template_dir = template_dir

    def convert_quiz(self, quiz, **kwargs):
        template = quizgen.util.file.read(os.path.join(self.template_dir, TEMPLATE_FILENAME_QUIZ))

        template = self.fill_metadata(template, quiz);

        groups = self.create_groups(quiz)
        template = self.fill_variable(template, TEMPLATE_VAR_GROUPS, groups)

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

        name = self.check_variable(group, 'name')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_NAME, group.name)

        points = self.check_variable(group, 'points')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_POINTS, str(group.points))

        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_NUMBER, str(number))

        question_type = self.check_variable(question, 'question_type')
        body = None

        if (question_type == quizgen.constants.QUESTION_TYPE_MULTIPLE_CHOICE):
            body = self.create_question_mcq(question)
        else:
            raise ValueError("Unsupported question type: '%s'." % (question_type))

        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_BODY, body)

        return template

    def create_question_mcq(self, question):
        filename = "%s_%s" % (quizgen.constants.QUESTION_TYPE_MULTIPLE_CHOICE, TEMPLATE_FILENAME_QUESTION)
        template = quizgen.util.file.read(os.path.join(self.template_dir, filename))

        prompt_document = self.check_variable(question, 'prompt_document')
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_PROMPT,
                question.prompt_document.to_format(self.format))

        answers = self.check_variable(question, 'answers')
        answers_text = self.create_answers_mcq(answers)
        template = self.fill_variable(template, TEMPLATE_VAR_QUESTION_ANSWERS, answers_text)

        return template

    def create_answers_mcq(self, answers):
        filename = "%s_%s" % (quizgen.constants.QUESTION_TYPE_MULTIPLE_CHOICE, TEMPLATE_FILENAME_ANSWER)
        base_template = quizgen.util.file.read(os.path.join(self.template_dir, filename))

        answers_text = []

        for answer in answers:
            template = base_template

            template = self.fill_variable(template, TEMPLATE_VAR_ANSWER_TEXT,
                    answer['document'].to_format(self.format))

            answers_text.append(template)

        return "\n\n".join(answers_text)

    def fill_metadata(self, template, quiz):
        title = self.check_variable(quiz, 'title')
        template = self.fill_variable(template, TEMPLATE_VAR_TITLE, title)

        course_title = self.check_variable(quiz, 'course_title')
        template = self.fill_variable(template, TEMPLATE_VAR_COURSE_TITLE, course_title)

        term_title = self.check_variable(quiz, 'term_title')
        template = self.fill_variable(template, TEMPLATE_VAR_TERM_TITLE, term_title)

        date = self.check_variable(quiz, 'date')
        template = self.fill_variable(template, TEMPLATE_VAR_DATE, date.strftime(DATE_FORMAT))

        template = self.fill_variable(template, TEMPLATE_VAR_DESCRIPTION,
                quiz.description_document.to_format(self.format))

        header = self.build_header(quiz)
        template = self.fill_variable(template, TEMPLATE_VAR_HEADER, header)

        return template

    def build_header(self, quiz):
        title = self.check_variable(quiz, 'title')

        header = [title]

        if (quiz.course_title != ''):
            header.append(quiz.course_title)

        if (quiz.term_title != ''):
            header.append(quiz.term_title)

        return ' -- '.join(header)

    def fill_variable(self, template, variable, value):
        return template.replace(variable, value)

    def check_variable(self, quiz, name):
        value = getattr(quiz, name, '')
        if ((value is None) or (value == '')):
            raise ValueError("Quiz is missing key value: '%s'." % (name))

        return value
