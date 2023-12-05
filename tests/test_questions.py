import glob
import json
import os

import quizgen.canvas
import quizgen.quiz
import tests.base

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
QUESTIONS_DIR = os.path.join(THIS_DIR, "questions")

QUESTIONS_FILENAME = 'question.json'
CANVAS_FILENAME = 'canvas.json'

CANVAS_TEST_GROUP_ID = 0
CANVAS_TEST_INDEX = 0

class QuestionsTest(tests.base.BaseTest):
    """
    Test parsing/generating all questions in the 'tests/questions' directory.
    A 'question.json' indicates a question that should be parsed.
    A 'canvas.json' in the same directory indicates that the question
    should also be checked for it's Canvas format.
    """

    pass

def _discover_question_tests():
    for path in sorted(glob.glob(os.path.join(QUESTIONS_DIR, "**", QUESTIONS_FILENAME), recursive = True)):
        try:
            _add_question_test(path)
        except Exception as ex:
            raise ValueError("Failed to parse test case '%s'." % (path)) from ex

def _add_question_test(path):
    base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

    test_name = 'test_parse_' + base_test_name
    setattr(QuestionsTest, test_name, _get_question_parse_test_method(path))

    canvas_path = os.path.join(os.path.dirname(path), CANVAS_FILENAME)
    if (os.path.exists(canvas_path)):
        test_name = 'test_canvas_' + base_test_name
        setattr(QuestionsTest, test_name, _get_question_canvas_test_method(path, canvas_path))

def _get_question_parse_test_method(path):
    def __method(self):
        question = quizgen.quiz.Question.from_path(path)
        self.assertIsNotNone(question)

    return __method

def _get_question_canvas_test_method(path, canvas_path):
    def __method(self):
        question = quizgen.quiz.Question.from_path(path)
        canvas_info = quizgen.canvas._create_question_json(CANVAS_TEST_GROUP_ID, question, CANVAS_TEST_INDEX)

        with open(canvas_path, 'r') as file:
            expected_canvas_info = json.load(file)

        self.assertJSONDictEqual(expected_canvas_info, canvas_info)

    return __method

_discover_question_tests()
