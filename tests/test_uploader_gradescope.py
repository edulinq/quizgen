import os

import quizgen.cli.gradescope.upload
import quizgen.latex
import quizgen.uploader.gradescope
import quizgen.util.httpsession
import tests.base

ALREADY_EXISTS_SESSION_NAME = 'gradescope-already-exists'

TEST_COURSE = '123456'
TEST_USER = 'test@test.edulinq.org'
TEST_PASS = 'abc123'

class TestUploaderGradescope(tests.base.BaseTest):
    """
    Test uploading GradeScope quizzes using recorded HTTP sessions.
    """

    def test_already_exists(self):
        if (not quizgen.latex.is_available()):
            self.skipTest("LaTeX is not available.")

        session_id = quizgen.uploader.gradescope.SESSION_ID_UPLOAD
        session_base_dir = os.path.join(tests.base.HTTP_SESSIONS_DIR, ALREADY_EXISTS_SESSION_NAME)

        quizgen.util.httpsession.load_test_session(session_id, session_base_dir)

        temp_dir = quizgen.util.dirent.get_temp_path('quizgen-test-')
        quiz_path = os.path.abspath(os.path.join(tests.base.GOOD_QUIZZES_DIR, 'single-question', 'quiz.json'))

        raw_args = [
            '--log-level', 'ERROR',
            '--course', TEST_COURSE,
            '--user', TEST_USER,
            '--pass', TEST_PASS,
            '--out', temp_dir,
            quiz_path,
        ]

        parser = quizgen.cli.gradescope.upload._get_parser()
        args = parser.parse_args(raw_args)

        quizgen.cli.gradescope.upload.run(args)
