"""
Convert a quiz into GradeScope-compatible TeX using templates.
"""

import os

import quizgen.constants
import quizgen.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'linqs-gradescope')

TEMPLATE_VAR_LEFT_TABLE = '{{{LEFT_MATCHING_TABLE}}}'
TEMPLATE_VAR_RIGHT_TABLE = '{{{RIGHT_MATCHING_TABLE}}}'

TEMPLATE_FILENAME_LEFT_TABLE = 'matching_question_left_table.template'
TEMPLATE_FILENAME_LEFT_TABLE_ROW = 'matching_question_left_table_row.template'
TEMPLATE_FILENAME_RIGHT_TABLE = 'matching_question_right_table.template'
TEMPLATE_FILENAME_RIGHT_TABLE_ROW = 'matching_question_right_table_row.template'

class GradeScopeTemplateConverter(quizgen.converter.template.TemplateConverter):
    def __init__(self, template_dir = DEFAULT_TEMPLATE_DIR, **kwargs):
        super().__init__(quizgen.constants.DOC_FORMAT_TEX, template_dir, **kwargs)

    # Override matching choice generation.
    def create_choices_matching(self, base_template, question_number, lefts, rights):
        right_ids = self.get_right_ids()
        if (len(rights) > len(right_ids)):
            raise ValueError("Too many distractors. Max allowed: '%d'." % (len(right_ids)))

        # The left and rights will be generated in different tables.
        left_table = self._create_matching_left_table(question_number, lefts)
        right_table = self._create_matching_right_table(question_number, rights, right_ids)

        template = base_template
        template = self.fill_variable(template, TEMPLATE_VAR_LEFT_TABLE, left_table)
        template = self.fill_variable(template, TEMPLATE_VAR_RIGHT_TABLE, right_table)

        return template

    def _create_matching_left_table(self, question_number, lefts):
        table_template = quizgen.util.file.read(os.path.join(self.template_dir, quizgen.converter.template.TEMPLATE_QUESTION_TYPES_DIR, TEMPLATE_FILENAME_LEFT_TABLE), strip = False)
        base_row_template = quizgen.util.file.read(os.path.join(self.template_dir, quizgen.converter.template.TEMPLATE_QUESTION_TYPES_DIR, TEMPLATE_FILENAME_LEFT_TABLE_ROW), strip = False)

        choices = []

        for i in range(len(lefts)):
            template = base_row_template

            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_QUESTION_NUMBER, str(question_number))
            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_LEFT, lefts[i])
            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_LEFT_ID, str(i))

            choices.append(template)

        table_template = self.fill_variable(table_template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_CHOICES, "\n".join(choices))

        return table_template

    def _create_matching_right_table(self, question_number, rights, right_ids):
        table_template = quizgen.util.file.read(os.path.join(self.template_dir, quizgen.converter.template.TEMPLATE_QUESTION_TYPES_DIR, TEMPLATE_FILENAME_RIGHT_TABLE), strip = False)
        base_row_template = quizgen.util.file.read(os.path.join(self.template_dir, quizgen.converter.template.TEMPLATE_QUESTION_TYPES_DIR, TEMPLATE_FILENAME_RIGHT_TABLE_ROW), strip = False)

        choices = []

        for i in range(len(rights)):
            template = base_row_template

            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_QUESTION_NUMBER, str(question_number))
            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_RIGHT, rights[i])
            template = self.fill_variable(template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_RIGHT_ID, right_ids[i])

            choices.append(template)

        table_template = self.fill_variable(table_template, quizgen.converter.template.TEMPLATE_VAR_ANSWER_CHOICES, "\n".join(choices))

        return table_template
