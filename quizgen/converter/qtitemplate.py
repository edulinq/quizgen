"""
Convert a quiz into QTI using templates.
"""

import os

import quizgen.constants
import quizgen.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-qti')

QUESTION_TYPE_MAP = {
    # Direct Mappings
    quizgen.constants.QUESTION_TYPE_ESSAY: 'essay_question',
    quizgen.constants.QUESTION_TYPE_FIMB: 'fill_in_multiple_blanks_question',
    quizgen.constants.QUESTION_TYPE_MATCHING: 'matching_question',
    quizgen.constants.QUESTION_TYPE_MA: 'multiple_answers_question',
    quizgen.constants.QUESTION_TYPE_MCQ: 'multiple_choice_question',
    quizgen.constants.QUESTION_TYPE_MDD: 'multiple_dropdowns_question',
    quizgen.constants.QUESTION_TYPE_NUMERICAL: 'numerical_question',
    quizgen.constants.QUESTION_TYPE_TEXT_ONLY: 'text_only_question',
    quizgen.constants.QUESTION_TYPE_TF: 'true_false_question',
    # Indirect Mappings
    quizgen.constants.QUESTION_TYPE_FITB: 'short_answer_question',
    quizgen.constants.QUESTION_TYPE_SA: 'essay_question',
}

class QTITemplateConverter(quizgen.converter.template.TemplateConverter):
    def __init__(self, template_dir = DEFAULT_TEMPLATE_DIR, **kwargs):
        super().__init__(quizgen.constants.FORMAT_HTML, template_dir, **kwargs)

    def modify_question_context(self, context, question, variant):
        context['question']['mapped_question_type'] = QUESTION_TYPE_MAP[question.question_type]

        return context

    # TEST - output full zipped format (only the main file right now).
