"""
Convert a quiz into HTML using templates.
"""

import os

import quizgen.constants
import quizgen.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-html')

class HTMLTemplateConverter(quizgen.converter.template.TemplateConverter):
    def __init__(self,
            format = quizgen.constants.FORMAT_HTML, template_dir = DEFAULT_TEMPLATE_DIR,
            **kwargs):
        super().__init__(format, template_dir, **kwargs)

    def clean_solution_content(self, document):
        return document.to_text()

class CanvasTemplateConverter(HTMLTemplateConverter):
    def __init__(self,
            template_dir = DEFAULT_TEMPLATE_DIR,
            **kwargs):
        super().__init__(quizgen.constants.FORMAT_CANVAS, template_dir, **kwargs)
