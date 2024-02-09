"""
Convert a quiz to JSON.
"""

import quizgen.converter.converter

class JSONConverter(quizgen.converter.converter.Converter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def convert_variant(self, variant, **kwargs):
        return variant.to_json()
