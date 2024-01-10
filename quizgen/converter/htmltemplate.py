"""
Convert a quiz into HTML using templates.
"""

import os

import quizgen.constants
import quizgen.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'linqs-html')

class HTMLTemplateConverter(quizgen.converter.template.TemplateConverter):
    def __init__(self, template_dir = DEFAULT_TEMPLATE_DIR, **kwargs):
        super().__init__(quizgen.constants.DOC_FORMAT_HTML, template_dir, **kwargs)

    # Override matching choice generation.
    def create_choices_matching(self, base_template, key_template, question_number, lefts, rights, matches):
        # The choices are the same for all answers.
        choices_text = self.create_matching_rights(rights)

        answers_text = []

        for i in range(len(lefts)):
            if (self.answer_key and (key_template is not None)):
                template = key_template
            else:
                template = base_template

            left = lefts[i]
            answer_id = "%d.%d" % (question_number, i)

            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_QUESTION_ID, str(question_number))
            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_ID, answer_id)
            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_TEXT, left)
            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_CHOICES, choices_text)

            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_SOLUTION, rights[matches[i]])

            answers_text.append(template)

        return "\n\n".join(answers_text)

    def create_matching_rights(self, rights):
        filename = "%s_%s" % (quizgen.constants.QUESTION_TYPE_MATCHING, quizgen.converter.template.TEMPLATE_FILENAME_CHOICE)
        base_template = quizgen.util.file.read(os.path.join(self.template_dir, quizgen.converter.template.TEMPLATE_QUESTION_TYPES_DIR, filename))

        choices_text = []

        for i in range(len(rights)):
            template = base_template
            right = rights[i]

            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_CHOICE_INDEX, str(i))
            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_CHOICE_TEXT, right)

            choices_text.append(template)

        return "\n\n".join(choices_text)
