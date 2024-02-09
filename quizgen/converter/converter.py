import abc

import quizgen.variant

class Converter(abc.ABC):
    def __init__(self, answer_key = False, **kwargs):
        super().__init__()

        self.answer_key = answer_key

    @abc.abstractmethod
    def convert_variant(self, variant, **kwargs):
        pass

    def convert_question(self, question, variant = None, **kwargs):
        """
        Convert a single question.
        If a variant is passed in, the converter will change it.
        """

        if (variant is None):
            variant = quizgen.variant.Variant.get_dummy()

        variant.questions = [question]

        return self.convert_variant(variant, **kwargs)
