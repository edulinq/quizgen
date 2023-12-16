"""
Convert a quiz into TeX using templates.
"""

import os

import quizgen.constants
import quizgen.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'linqs-tex')

class TexTemplateConverter(quizgen.converter.template.TemplateConverter):
    def __init__(self, template_dir = DEFAULT_TEMPLATE_DIR, **kwargs):
        super().__init__(quizgen.constants.DOC_FORMAT_TEX, template_dir, **kwargs)

    def get_left_ids(self):
        return [r'\underline{\hspace{1cm}}'] * len(self.get_right_ids())
