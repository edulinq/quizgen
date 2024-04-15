"""
Test the typing system itself.
"""

import json

import quizgen.jtype.constants
import quizgen.jtype.validator
import quizgen.util.file
import tests.base

class TestJType(tests.base.BaseTest):
    def test_self_type_validation(self):
        # Test the the type definition validates against itself.
        # To do this, we must look at each field definition as its own document.
        base_type = json.loads(quizgen.util.file.read(quizgen.jtype.constants.METATYPE_PATH))

        for (key, value) in base_type['fields'].items():
            try:
                quizgen.jtype.validator.validate(base_type, value, raise_on_error = True)
            except Exception as ex:
                raise ValueError("Field Definition: '%s'" % (key)) from ex
