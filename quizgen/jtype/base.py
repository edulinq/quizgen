import abc
import json

import json5

import quizgen.jtype.constants
import quizgen.jtype.validator
import quizgen.util.file

class JTyped(abc.ABC):
    """
    The JTyped ("JSON-Typed") abstract class defines classes that have the ability to serialize to a dict/JSON,
    and be validated by a JSON type definition.
    These classes should also have to ability to deserialize from a JSON string/dict.
    """

    @abc.abstractmethod
    def get_jtype_def(self):
        """
        Get a dict representing a valid jtype definition.
        """

        pass

    @abc.abstractmethod
    def to_dict(self, **kwargs):
        pass

    def to_json(self, indent = 4, **kwargs):
        return json.dumps(self.to_dict(**kwargs), indent = indent)

    def to_file(self, path, **kwargs):
        content = self.to_json(**kwargs)
        quizgen.util.file(path, content)

    def validate_jtype(self, raise_on_error = False, to_dict_args = {}):
        definition = self.get_jtype_def()
        content = self.to_json(**kwargs)
        return quizgen.jtype.validator.validate(definition, content, raise_on_error = raise_on_error)

    @staticmethod
    @abc.abstractmethod
    def from_path(path, **kwargs):
        pass

    @staticmethod
    @abc.abstractmethod
    def from_dict(path, **kwargs):
        pass
