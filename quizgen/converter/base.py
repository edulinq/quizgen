import abc

class QuizConverter(abc.ABC):
    def __init__(self, **kwargs):
        pass

    @abc.abstractmethod
    def convert_quiz(self, quiz, **kwargs):
        pass
