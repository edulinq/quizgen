import abc

class Converter(abc.ABC):
    def __init__(self, answer_key = False, **kwargs):
        super().__init__()

        self.answer_key = answer_key

    @abc.abstractmethod
    def convert_variant(self, variant, **kwargs):
        pass
