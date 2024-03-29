import logging

import quizgen.log
import tests.base

class TestLog(tests.base.BaseTest):
    def test_base_levels(self):
        quizgen.log.init()

        print()
        logging.debug("log test: debug")
        logging.info("log test: info")
        logging.warning("log test: warning")
        logging.error("log test: error")
