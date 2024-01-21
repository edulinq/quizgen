import logging

import quizgen.log
import tests.base

class TestGit(tests.base.BaseTest):
    def test_base_levels(self):
        quizgen.log.init()

        logging.debug("debug")
        logging.info("info")
        logging.warning("warning")
        logging.error("error")
