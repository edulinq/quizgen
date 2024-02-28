"""
Convert a quiz into QTI using templates.
"""

import logging
import os
import warnings
import zipfile

import bs4

import quizgen.constants
import quizgen.converter.template
import quizgen.util.file

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

TEMPLATE_FILENAME_ASSESSMENT_META = 'qti_assessment_meta.template'
TEMPLATE_FILENAME_MANIFEST = 'qti_imsmanifest.template'

OUT_FILENAME_QUIZ = 'quiz.xml'
OUT_FILENAME_ASSESSMENT_META = 'assessment_meta.xml'
OUT_FILENAME_MANIFEST = 'imsmanifest.xml'

class QTITemplateConverter(quizgen.converter.template.TemplateConverter):
    def __init__(self, template_dir = DEFAULT_TEMPLATE_DIR, **kwargs):
        super().__init__(quizgen.constants.FORMAT_HTML, template_dir,
                jinja_filters = {
                    'to_xml': _to_xml,
                },
                **kwargs)

    def convert_variant(self, variant, **kwargs):
        # Parse and format the XML.
        text = super(QTITemplateConverter, self).convert_variant(variant, **kwargs)
        return self._format_xml(text)

    def modify_question_context(self, context, question, variant):
        context['question']['mapped_question_type'] = QUESTION_TYPE_MAP[question.question_type]
        return context

    def convert_quiz(self, quiz, out_dir = '.', **kwargs):
        # TEST
        variant = quiz.create_variant(**kwargs)

        temp_dir = quizgen.util.file.get_temp_path(prefix = 'quizgen-qti-')
        temp_dir = os.path.join(temp_dir, quiz.title)
        os.makedirs(temp_dir, exist_ok = True)

        path = os.path.join(temp_dir, OUT_FILENAME_QUIZ)
        quizgen.util.file.write(path, self.convert_variant(variant, **kwargs))

        self._convert_assessment_meta(quiz, temp_dir)
        self._convert_manifest(quiz, temp_dir)

        path = os.path.join(out_dir, "%s.qti.zip" % (quiz.title))
        self._create_zip(quiz, path, temp_dir)

        logging.info("Created QTI quiz at '%s'." % (path))
        return path

    def _create_zip(self, quiz, path, temp_dir):
        with zipfile.ZipFile(path, mode = 'w') as archive:
            for filename in [OUT_FILENAME_QUIZ, OUT_FILENAME_ASSESSMENT_META, OUT_FILENAME_MANIFEST]:
                in_path = os.path.join(temp_dir, filename)
                name = '/'.join([quiz.title, filename])
                archive.write(in_path, arcname = name)

    def _format_xml(self, text):
        warnings.filterwarnings('ignore', category = bs4.builder.XMLParsedAsHTMLWarning)
        document = bs4.BeautifulSoup(text, 'html.parser')
        return document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

    def _convert_assessment_meta(self, quiz, out_dir):
        template = self.env.get_template(TEMPLATE_FILENAME_ASSESSMENT_META)

        quiz_context = quiz.to_dict(include_docs = False)
        quiz_context['description_text'] = quiz.description_document.to_format(self.format)

        text = template.render(quiz = quiz_context)
        text = self._format_xml(text)

        path = os.path.join(out_dir, OUT_FILENAME_ASSESSMENT_META)
        quizgen.util.file.write(path, text)

    def _convert_manifest(self, quiz, out_dir):
        template = self.env.get_template(TEMPLATE_FILENAME_MANIFEST)

        quiz_context = quiz.to_dict(include_docs = False)

        text = template.render(quiz = quiz_context)
        text = self._format_xml(text)

        path = os.path.join(out_dir, OUT_FILENAME_MANIFEST)
        quizgen.util.file.write(path, text)

def _to_xml(item):
    """
    Convert the item to an XML string.
    """

    if (item is None):
        return ''

    if (isinstance(item, bool)):
        return str(item).lower()

    return str(item)
