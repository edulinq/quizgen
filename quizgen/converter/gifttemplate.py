"""
Convert a quiz into GIFT using templates.
"""

import os

import quizgen.constants
import quizgen.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-gift')

JINJA_OPTIONS = {
    'trim_blocks': True,
    'lstrip_blocks': True,
    'keep_trailing_newline': False,
}

class GIFTTemplateConverter(quizgen.converter.template.TemplateConverter):
    def __init__(self, template_dir = DEFAULT_TEMPLATE_DIR, **kwargs):
        super().__init__(quizgen.constants.FORMAT_MD, template_dir,
                jinja_options = JINJA_OPTIONS,
                jinja_filters = {
                    'gift_compact': gift_compact,
                },
                **kwargs)

def gift_compact(text, *args, **kwargs):
    """
    The GIFT format wants questions to have no blank lines in them.
    """

    text = text.strip()
    text = text.replace("\n\n", "\n\\n")

    return text
