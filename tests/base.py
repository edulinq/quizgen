import glob
import json
import os
import unittest

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
QUESTIONS_DIR = os.path.join(THIS_DIR, "questions")
GOOD_QUESTIONS_DIR = os.path.join(QUESTIONS_DIR, "good")
BAD_QUESTIONS_DIR = os.path.join(QUESTIONS_DIR, "bad")

QUESTIONS_FILENAME = 'question.json'

class BaseTest(unittest.TestCase):
    def assertJSONDictEqual(self, expected, actual):
        expected_json = json.dumps(expected, indent = 4)
        actual_json = json.dumps(actual, indent = 4)

        message = f"\n---\nExpected: {expected_json}\n###\nActual: {actual_json}\n---\n"
        self.assertDictEqual(expected, actual, msg = message)

def discover_question_tests():
    good_paths = list(sorted(glob.glob(os.path.join(GOOD_QUESTIONS_DIR, "**", QUESTIONS_FILENAME), recursive = True)))
    bad_paths = list(sorted(glob.glob(os.path.join(BAD_QUESTIONS_DIR, "**", QUESTIONS_FILENAME), recursive = True)))

    return good_paths, bad_paths
