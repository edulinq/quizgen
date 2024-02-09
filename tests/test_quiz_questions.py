import glob
import os

import quizgen.converter.htmltemplate
import quizgen.converter.json
import quizgen.converter.textemplate
import quizgen.quiz
import tests.base

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

CONVERTERS = [
    quizgen.converter.json.JSONConverter,
    quizgen.converter.textemplate.TexTemplateConverter,
    quizgen.converter.htmltemplate.HTMLTemplateConverter,
]

class QuizQuestionsTest(tests.base.BaseTest):
    """
    Compile all the good test quiz question into a quiz and test that quiz.
    """

    _quiz = None
    _num_paths = -1

    @classmethod
    def setUpClass(cls):
        good_paths, _ = tests.base.discover_question_tests()

        quiz_info = {
            'title': 'Test Quiz',
            'course_title': "Test Course",
            'term_title': "Test Term",
            'description': 'testing',
            'version': '0.0.0',
            'groups': [],
        }

        for path in good_paths:
            name = os.path.basename(os.path.dirname(path))

            quiz_info['groups'].append({
                'name': name,
                'questions': [path],
            })

        QuizQuestionsTest._quiz = quizgen.quiz.Quiz.from_dict(quiz_info, THIS_DIR)
        QuizQuestionsTest._num_paths = len(good_paths)

    def testNumQuestions(self):
        self.assertEqual(QuizQuestionsTest._num_paths, QuizQuestionsTest._quiz.num_questions())

def _add_converter_tests():
    for converter in CONVERTERS:
        for key in [True, False]:
            for shuffle in [True, False]:
                test_name = 'test_converter__%s__key_%s__shuffle_%s' % (converter.__name__, str(key), str(shuffle))
                setattr(QuizQuestionsTest, test_name, _get_template_test(converter, key, shuffle))

def _get_template_test(converter_class, key, shuffle):
    def __method(self):
        converter = converter_class(answer_key = key)

        variant = QuizQuestionsTest._quiz.create_variant(all_questions = True)
        variant.shuffle_answers = shuffle

        content = converter.convert_variant(variant)
        self.assertTrue(len(content) > 10)

    return __method

_add_converter_tests()
