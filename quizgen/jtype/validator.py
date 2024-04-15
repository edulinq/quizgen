"""
Provide functionality for validating content with a jtype definition.
"jtype" is the name given to the specific type specification we are working with and
is only defined and used internally to the quizgen project.
"""

import logging
import os
import re

import json5

import quizgen.jtype.constants

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

KEY_DEFAULT = 'default'
KEY_FIELDS = 'fields'
KEY_IGNORE_EXTRA_FIELDS = 'ignore_extra_fields'
KEY_JTYPE_DEF = 'jtype_def'
KEY_NAME = 'name'
KEY_REQUIRED = 'required'
KEY_TYPE = 'type'
KEY_VALUES = 'values'

DEFAULT_DEFAULT = None
DEFAULT_IGNORE_EXTRA_FIELDS = False
DEFAULT_REQUIRED = False

# Simple strings must match this regex.
SIMPLE_STRING_REGEX = r'^[a-zA-Z0-9\-\.,!\? ]*$'

# Parsed strings (in dict form) should have exactly type keys.
PARSED_STRING_DICT_KEYS = list(sorted([
    'text',
    'document',
]))

TYPE_VALUE_ANY = 'any'

TYPE_VALUE_BOOLEAN = 'boolean'

TYPE_VALUE_LIST = 'list'
TYPE_VALUE_MAP = 'map'

TYPE_VALUE_ENUM_STRING = 'enum_string'
TYPE_VALUE_PARSED_STRING = 'parsed_string'
TYPE_VALUE_SIMPLE_STRING = 'simple_string'

TYPE_VALUE_FLOAT = 'float'
TYPE_VALUE_INT = 'int'
TYPE_VALUE_NUMBER = 'number'

TYPE_VALUE_EXISTING_DIR = 'existing_dir'
TYPE_VALUE_EXISTING_FILE = 'existing_file'
TYPE_VALUE_EXISTING_PATH = 'existing_path'
TYPE_VALUE_PATH = 'path'

TYPE_VALUE_JTYPE = 'jtype'

TYPE_MAP = {
    TYPE_VALUE_BOOLEAN: bool,

    TYPE_VALUE_LIST: list,
    TYPE_VALUE_MAP: dict,

    TYPE_VALUE_ENUM_STRING: str,
    TYPE_VALUE_PARSED_STRING: (str, dict),
    TYPE_VALUE_SIMPLE_STRING: str,

    TYPE_VALUE_FLOAT: float,
    TYPE_VALUE_INT: int,
    TYPE_VALUE_NUMBER: (int, float),

    TYPE_VALUE_EXISTING_DIR: str,
    TYPE_VALUE_EXISTING_FILE: str,
    TYPE_VALUE_EXISTING_PATH: str,
    TYPE_VALUE_PATH: str,
}

TYPE_SET_NUMBER = [
    TYPE_VALUE_FLOAT,
    TYPE_VALUE_INT,
    TYPE_VALUE_NUMBER,
]

TYPE_SET_STRING = [
    TYPE_VALUE_ENUM_STRING,
    TYPE_VALUE_PARSED_STRING,
    TYPE_VALUE_SIMPLE_STRING,
]

TYPE_SET_PATH = [
    TYPE_VALUE_EXISTING_DIR,
    TYPE_VALUE_EXISTING_FILE,
    TYPE_VALUE_EXISTING_PATH,
    TYPE_VALUE_PATH,
]

def validate(definition, content, **kwargs):
    """
    See _Validator.__init__() for allowed kwargs.

    Validate an object (dict) according to the specified jtype definition.
    |raise_on_error| will control if this function will raise a ValidationError or return False
    when an invalid object is encoutered.
    On success, True will be returned.

    If |base_dir| is provided, then existing path types with relative values will be validated using it as the base.
    """

    validator = _Validator(definition, content, **kwargs)
    return validator.validate()

class _Validator(object):
    def __init__(self, definition, content,
            raise_on_error = False, log_on_error = False,
            ignore_extra_fields = DEFAULT_IGNORE_EXTRA_FIELDS,
            base_dir = None,
            **kwargs):
        self.definition = definition
        self.content = content
        self.raise_on_error = raise_on_error
        self.log_on_error = log_on_error
        self.ignore_extra_fields = ignore_extra_fields
        self.base_dir = base_dir

    def validate(self):
        self.definition = self._check_initial_type(self.definition, 'definition')
        self.content = self._check_initial_type(self.content, 'content')
        if ((self.definition is False) or (self.content is False)):
            return False

        self.ignore_extra_fields = self.definition.get(KEY_IGNORE_EXTRA_FIELDS, self.ignore_extra_fields)

        return self._check_fields()

    def _check_fields(self):
        definition_field_names = set(self.definition[KEY_FIELDS].keys())
        content_field_names = set(self.content.keys())

        extra_names = content_field_names - definition_field_names
        if ((not self.ignore_extra_fields) and (len(extra_names) > 0)):
            return self._fail("Extra fields found that were not in the type definition: %s." % (list(sorted(extra_names))))

        for name in self.definition[KEY_FIELDS]:
            valid = self._check_field(name)
            if (not valid):
                return False

        return True

    def _check_field(self, field_name):
        field_definition = self.definition[KEY_FIELDS][field_name]
        value = self.content.get(field_name, DEFAULT_DEFAULT)

        if (field_name not in self.content):
            required = field_definition.get(KEY_REQUIRED, DEFAULT_REQUIRED)
            if (required):
                return self._fail("Required field '%s' is missing." % (field_name))

            value = field_definition.get(KEY_DEFAULT, DEFAULT_DEFAULT)

        # The value is either real or from the default (or default default).

        if (KEY_VALUES in field_definition):
            if (value not in field_definition[KEY_VALUES]):
                return self._fail("Field '%s' has value '%s', which is not one of the allowed values: '%s'." % (field_name, str(value), list(map(str, field_definition[KEY_VALUES]))))

        jtype_subdefinition = field_definition.get(KEY_JTYPE_DEF, None)
        return self._check_type(field_name, value, field_definition[KEY_TYPE], jtype_subdefinition)

    def _check_type(self, field_name, value, type_definition, sub_definition):
        # Empty/Null/None values are always allowed.
        if (value is None):
            return True

        if (type_definition == TYPE_VALUE_ANY):
            return True

        # This value is validated by another JTYPE definition.
        if (type_definition == TYPE_VALUE_JTYPE):
            if (jtype_subdefinition is None):
                return self._fail("Field '%s' is validated by a JType definition, but definition ('%s' field) is missing." % (field_name, KEY_JTYPE_DEF))

            return validate(jtype_subdefinition, value,
                raise_on_error = self.raise_on_error, log_on_error = self.log_on_error,
                ignore_extra_fields = self.ignore_extra_fields,
                base_dir = self.base_dir)

        # Check that the value's type matches without any semantics.
        # The special types (any and jtype) have already been dealt with.
        basic_type = TYPE_MAP.get(type_definition, None)
        if (basic_type is None):
            # This is our error, not a validation error.
            raise ValueError("Unknown type: '%s'." % (type_definition))

        if (not isinstance(value, basic_type)):
            return self._fail("Field '%s' has an incorrect type '%s', expected '%s'." % (field_name, str(type(value)), str(basic_type)))

        if (type_definition in TYPE_SET_STRING):
            return self._check_string(field_name, value, type_definition)
        elif (type_definition in TYPE_SET_PATH):
            return self._check_path(field_name, value, type_definition)

        return True

    def _check_string(self, field_name, value, type_definition):
        if (type_definition == TYPE_VALUE_ENUM_STRING):
            return True

        # Simple strings are limited on the content they can have.
        if (type_definition == TYPE_VALUE_SIMPLE_STRING):
            match = re.search(SIMPLE_STRING_REGEX, value)
            if (match is not None):
                return True

            return self._fail("Field '%s' has a simple string with disallowed characters. Simple strings must follow the regex '%s', found: '%s'." % (field_name, SIMPLE_STRING_REGEX, value))

        # Parsed strings must either just be the base string,
        # or a dict with 'text' and 'document' keys (indicating that it has already been parsed).
        # The strings will not be parsed to check for syntax.
        if (type_definition == TYPE_VALUE_PARSED_STRING):
            if (isinstance(value, str)):
                return True

            if (not isinstance(value, dict)):
                self._fail("Field '%s' is a parsed string and must either be a dict or str, found '%s'." % (field_name, str(type(value))))

            keys = list(sorted(value.keys()))
            if (keys != PARSED_STRING_DICT_KEYS):
                self._fail("Field '%s' is a parsed string (dict form) and must have the keys '%s', found keys '%s'." % (field_name, PARSED_STRING_DICT_KEYS, keys))

            return True

        raise ValueError("Unknown string type: '%s'." % (type_definition))

    def _check_path(self, field_name, value, type_definition):
        if (type_definition == TYPE_VALUE_PATH):
            return True

        path = value
        if (not os.path.isabs(path)):
            # If the path is relative, then either don't validate it (if base_dir is empty),
            # or join with base_dir to form a complete path.
            if (self.base_dir is None):
                return True

            path = os.path.join(self.base_dir, path)

        if (not os.path.exists(value)):
            return self._fail("Field '%s' points to a non-existent path: '%s'." % (field_name, path))

        if (type_definition == TYPE_VALUE_EXISTING_PATH):
            return True

        is_dir = os.path.isdir(path)
        want_dir = (type_definition == TYPE_VALUE_EXISTING_DIR)

        if (want_dir):
            if (is_dir):
                return True

            return self._fail("Field '%s' should point to a directory, but points to a file: '%s'." % (field_name, path))

        if (is_dir):
            return self._fail("Field '%s' should point to a file, but points to a directory: '%s'." % (field_name, path))

        return True

    def _check_initial_type(self, value, label):
        if (isinstance(value, str)):
            value = json5.loads(value)

        if (not isinstance(value, dict)):
            return _fail("Input '%s' is not a dict." % (label))

        return value

    def _fail(self, reason):
        if (self.log_on_error):
            logging.warning(reason)

        if (self.raise_on_error):
            raise ValidationError(reason)

        return False

class ValidationError(Exception):
    pass
