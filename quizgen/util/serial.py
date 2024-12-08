import abc
import copy as pycopy
import datetime
import json
import os

import json5

import quizgen.util.file

class PODSerializer(abc.ABC):
    @abc.abstractmethod
    def to_pod(self, **kwargs):
        """
        Create a "Plain Old Data" representation of this object.
        """

        pass

class JSONSerializer(PODSerializer):
    """
    A base class that can automatically handle serialization.
    Deserialization is harder (and requires validation),
    so will be left as abstract.
    """

    def __init__(self, _skip_all_validation = False, _skip_class_validations = [], **kwargs):
        self._skip_all_validation = _skip_all_validation

        # Keep track of the classes that have been validated, so they can be skipped.
        self._validated_classes = {}

        for cls in _skip_class_validations:
            self._validated_classes[cls] = True

    def validate(self, cls = None, **kwargs):
        """
        A wrapper for validation.
        This should be called by child classes in their constructor.
        If cls is provided, then that specific _validate will be called.
        Otherwise, whatever default _validate() is registered for self's class will be called.
        This method should raise an exception if the object is invalid,
        and set self._validated_classes[cls] = True if the object is valid.
        """

        if (self._skip_all_validation):
            return

        if (cls is None):
            cls = self.__class__

        if (self._validated_classes.get(cls, False)):
            return

        cls._validate(self, **kwargs)
        self._validated_classes[cls] = True

    @abc.abstractmethod
    def _validate(self, **kwargs):
        """
        The true validation implementation.
        """

        pass

    def to_pod(self, **kwargs):
        return self.to_dict(**kwargs)

    def to_dict(self, copy = True, **kwargs):
        """
        Convert self to a dictonary that can easily be serialized.
        See _serialize() for all the keyword arguments.
        """

        data = self.__dict__

        if (copy):
            data = pycopy.deepcopy(data)

        return _serialize(data, **kwargs)

    def to_json(self, indent = 4, sort_keys = True, **kwargs):
        data = self.to_dict(**kwargs)
        return json.dumps(data, indent = indent, sort_keys = sort_keys)

    def to_path(self, path, **kwargs):
        quizgen.util.file.write(path, self.to_json(**kwargs))

    @classmethod
    def from_dict(cls, data, copy = True, extra_fields = {}, **kwargs):
        return _from_dict(cls, data, copy = copy, extra_fields = extra_fields, **kwargs)

    @classmethod
    def from_path(cls, path, add_base_dir = True, **kwargs):
        with open(path, 'r') as file:
            data = json5.load(file)

        if (('base_dir' not in data) and add_base_dir):
            data['base_dir'] = os.path.dirname(os.path.abspath(path))

        return cls.from_dict(data, copy = False, **kwargs)

def _from_dict(cls, data, copy = True, extra_fields = {}, **kwargs):
    if (copy):
        data = pycopy.deepcopy(data)

    for (key, value) in extra_fields.items():
        data[key] = value

    return cls(**data)

def _serialize(item,
        skip_private = True,
        convert_serializers = True,
        convert_dates = True,
        recursive = True,
        **kwargs):
    """
    Generally convert an object into a form better suited to serialization.
    """

    kwargs['skip_private'] = skip_private
    kwargs['convert_serializers'] = convert_serializers
    kwargs['convert_dates'] = convert_dates
    kwargs['recursive'] = recursive

    if (isinstance(item, PODSerializer) and convert_serializers):
        return item.to_pod(**kwargs)
    elif (isinstance(item, list) and recursive):
        return [_serialize(value, **kwargs) for value in item]
    elif (isinstance(item, dict) and recursive):
        return {key: _serialize(value, **kwargs) for (key, value) in item.items() if (not (skip_private and key.startswith('_')))}
    elif (isinstance(item, (datetime.date, datetime.time, datetime.datetime)) and convert_dates):
        return item.isoformat()

    return item
