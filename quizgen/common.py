import json

class QuizValidationError(ValueError):
    def __init__(self, message, ids = {}):
        parsed_ids = {}
        for (key, value) in ids.items():
            if ((value is None) or (value == '')):
                continue

            parsed_ids[key] = value

        if (len(parsed_ids) > 0):
            message = "%s %s" % (message, json.dumps(parsed_ids))

        super().__init__(message)
