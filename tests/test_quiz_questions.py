import glob
import os

import quizgen.converter.textemplate
import quizgen.quiz
import tests.base

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

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

    def testToJSON(self):
        content = QuizQuestionsTest._quiz.to_json()
        self.assertTrue(len(content) > 10)

    def testToTex(self):
        converter = quizgen.converter.textemplate.TexTemplateConverter()
        content = converter.convert_quiz(QuizQuestionsTest._quiz)
        self.assertTrue(len(content) > 10)
