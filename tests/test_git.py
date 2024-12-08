import os

import quizgen.util.dirent
import quizgen.util.git
import tests.base

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

class TestGit(tests.base.BaseTest):
    def test_in_repo(self):
        # This test should live inside a repo.
        version = quizgen.util.git.get_version(THIS_DIR)
        self.assertNotEqual(quizgen.util.git.UNKNOWN_VERSION, version, 'Got an unknown version. (This can also happen if this instance of the quizgen project is not in a git repo.')

    def test_cwd(self):
        # The tests should be run in a repo (this project repo).
        version = quizgen.util.git.get_version()
        self.assertNotEqual(quizgen.util.git.UNKNOWN_VERSION, version, 'Got an unknown version. (This can also happen if the tests are not being run inside of a git repo.')

    def test_not_in_repo(self):
        # A new temp dir should not be in a git repo.
        path = quizgen.util.dirent.get_temp_path(prefix = 'quizgen-test-git-')
        version = quizgen.util.git.get_version(path)
        self.assertEqual(quizgen.util.git.UNKNOWN_VERSION, version)
