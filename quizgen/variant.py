import quizgen.common
import quizgen.quiz

DUMMY_QUIZ_DATA = {
    'title': 'Dummy Title',
    'description': 'Dummy description.',
    'course_title': 'Dummy Course',
    'term_title': 'Dummy Term',
    'version': '0.0.0',
}

DUMMY_GROUP_DATA = {
    'name': 'Dummy Question',
}

class Variant(quizgen.quiz.Quiz):
    """
    A quiz varint is an instantiation of a quiz with specific set of questions chosen for each group.
    Variants still have question groups, but each group must only have the exact number of questions required for each group
    (or it is a validation error).

    Variants created directly from quizzes (as opposed to from a JSON file)
    will already have all the correct components, and will therefore only be lightly validated.
    Quizzes created from files will undergo full validation.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate(cls = Variant, **kwargs)

    def _validate(self, **kwargs):
        # Ensure that each group has the correct number of questions.
        for i in range(len(self.groups)):
            group = self.groups[i]

            if (len(group.questions) != group.pick_count):
                raise quizgen.common.QuizValidationError("Group at index %d (%s) has %d questions, expecting exactly %d." % (i, group.name, len(group.questions), group.pick_count))

    @staticmethod
    def get_dummy(question):
        """
        Get a "dummy" variant that has no real information.
        """

        quiz_data = DUMMY_QUIZ_DATA.copy()
        group_data = DUMMY_GROUP_DATA.copy()

        group_data['questions'] = [question]
        group_data['_skip_class_validations'] = [quizgen.group.Group]
        quiz_data['groups'] = [quizgen.group.Group(**group_data)]

        return Variant(**quiz_data)
