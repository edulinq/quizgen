"""
Convert a quiz into HTML using templates.
"""

import os

import quizgen.constants
import quizgen.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-html')

class HTMLTemplateConverter(quizgen.converter.template.TemplateConverter):
    def __init__(self, template_dir = DEFAULT_TEMPLATE_DIR, **kwargs):
        super().__init__(quizgen.constants.DOC_FORMAT_HTML, template_dir, **kwargs)

    def clean_solution_content(self, document):
        """
        An opportunity for children to clean the text of a solution before it is entered into a key.
        For example, tex solutions are hacky and cannot use certain functions.
        """

        return document.to_text()
