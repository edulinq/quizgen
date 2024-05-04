import glob
import json
import os
import unittest

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

QUESTIONS_DIR = os.path.join(THIS_DIR, "questions")
GOOD_QUESTIONS_DIR = os.path.join(QUESTIONS_DIR, "good")
BAD_QUESTIONS_DIR = os.path.join(QUESTIONS_DIR, "bad")

DOCUMENTS_DIR = os.path.join(THIS_DIR, 'documents')
GOOD_DOCUMENTS_DIR = os.path.join(DOCUMENTS_DIR, "good")
BAD_DOCUMENTS_DIR = os.path.join(DOCUMENTS_DIR, "bad")

QUESTIONS_FILENAME = 'question.json'

class BaseTest(unittest.TestCase):
    # See full diffs regardless of size.
    maxDiff = None

    def assertJSONDictEqual(self, expected, actual):
        expected_json = json.dumps(expected, indent = 4, sort_keys = True)
        actual_json = json.dumps(actual, indent = 4, sort_keys = True)

        message = f"\n---\nExpected: {expected_json}\n###\nActual: {actual_json}\n---\n"
        self.assertDictEqual(expected, actual, msg = message)

def discover_question_tests():
    good_paths = list(sorted(glob.glob(os.path.join(GOOD_QUESTIONS_DIR, "**", QUESTIONS_FILENAME), recursive = True)))
    bad_paths = list(sorted(glob.glob(os.path.join(BAD_QUESTIONS_DIR, "**", QUESTIONS_FILENAME), recursive = True)))

    return good_paths, bad_paths

def discover_good_document_files():
    return list(sorted(glob.glob(os.path.join(GOOD_DOCUMENTS_DIR, "**", "*.json"), recursive = True)))

def discover_bad_document_files():
    return list(sorted(glob.glob(os.path.join(BAD_DOCUMENTS_DIR, "**", "*.json"), recursive = True)))
