import json
import unittest

class BaseTest(unittest.TestCase):
    def assertJSONDictEqual(self, expected, actual):
        expected_json = json.dumps(expected, indent = 4)
        actual_json = json.dumps(actual, indent = 4)

        message = f"\n---\nExpected: {expected_json}\n###\nActual: {actual_json}\n---\n"
        self.assertDictEqual(expected, actual, msg = message)
