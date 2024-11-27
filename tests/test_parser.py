import json
import os
import re

import bs4

import quizgen.constants
import quizgen.parser.common
import quizgen.parser.math
import quizgen.parser.public
import tests.base

class TestParser(tests.base.BaseTest):
    """
    Test parsing.
    Good and bad situations will be loaded below into individual test cases.
    """

    # Show full output on large string diffs.
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        # Disable KaTeX for testing.
        quizgen.parser.math._katex_available = False
        pass

    @classmethod
    def tearDownClass(cls):
        quizgen.parser.math._katex_available = None
        pass

def _add_good_parse_questions():
    for path in tests.base.discover_good_document_files():
        with open(path, 'r') as file:
            documents = json.load(file)

        base_dir = os.path.dirname(path)

        for document in documents:
            name = document['name']
            text = document['text']

            for (doc_format, expected) in document['formats'].items():
                test_name = _make_name('good_parse', path, name, doc_format)
                options = document.get('options', {}).get(doc_format, {})
                context = document.get('context', {})
                setattr(TestParser, test_name, _get_good_parse_test(text, doc_format, expected, base_dir, options, context))

def _get_good_parse_test(text, doc_format, base_expected, base_dir, options, context):
    def __method(self):
        document = quizgen.parser.public.parse_text(text).document
        result = document.to_format(doc_format, base_dir = base_dir, include_metadata = False, **context)

        if (doc_format == quizgen.constants.FORMAT_JSON):
            result = json.loads(result)
            expected = {
                'type': 'document',
                'ast': {
                    'type': 'root',
                },
            }

            expected_children = []
            if (len(base_expected) > 0):
                if (isinstance(base_expected, list)):
                    expected_children += base_expected
                elif (isinstance(base_expected, dict)):
                    expected_children.append(base_expected)
                else:
                    raise ValueError("Unkown type for expected children: '%s'.", type(base_expected))

            if (len(expected_children) > 0):
                # If the first node is not the root block, then automatically insert it.
                if (not expected_children[0].get(quizgen.parser.common.TOKEN_META_KEY_ROOT, False)):
                    expected_children = [{
                        'type': 'container_block',
                        quizgen.parser.common.TOKEN_META_KEY_ROOT: True,
                        'children': expected_children,
                    }]

                expected['ast']['children'] = expected_children

            self.assertJSONDictEqual(expected, result)
        elif (doc_format == quizgen.constants.FORMAT_HTML):
            # If the HTML does not have a root block, then add one.
            raw_expected = base_expected.strip()
            if ((raw_expected != '') and ('qg-root-block' not in raw_expected)):
                raw_expected = '<div class="qg-root-block qg-block">' + raw_expected + '</div>'

            document = bs4.BeautifulSoup(raw_expected, 'html.parser')
            expected = document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

            document = bs4.BeautifulSoup(result, 'html.parser')
            result = document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

            expected, result = _apply_text_options(options, expected, result)
            self.assertLongStringEqual(expected, result)
        else:
            expected = base_expected.strip()
            result = result.strip()

            expected, result = _apply_text_options(options, expected, result)
            self.assertEqual(expected, result)

    return __method

def _add_bad_parse_questions():
    for path in tests.base.discover_bad_document_files():
        with open(path, 'r') as file:
            documents = json.load(file)

        base_dir = os.path.dirname(path)

        for document in documents:
            name = document['name']
            text = document['text']
            options = document.get('options', {})

            test_name = _make_name('bad_parse', path, name)
            setattr(TestParser, test_name, _get_bad_parse_test(text, base_dir, options))

def _get_bad_parse_test(text, base_dir, options):
    def __method(self):
        try:
            quizgen.parser.public.parse_text(text)
        except Exception:
            # Expected.
            return

        self.fail("Failed to raise an exception.")

    return __method

def _make_name(prefix, path, name, doc_format = None):
    clean_name = name.lower().strip().replace(' ', '_')
    clean_name = re.sub(r'\W+', '', clean_name)

    filename = os.path.splitext(os.path.basename(path))[0]

    test_name = "test_%s__%s__%s" % (prefix, filename, clean_name)

    if (doc_format is not None):
        test_name += ('__' + doc_format)

    return test_name

def _apply_text_options(options, a, b):
    if (options.get("ignore-whitespace", False)):
        a = re.sub(r'\s+', '', a)
        b = re.sub(r'\s+', '', b)

    return a, b

_add_bad_parse_questions()
_add_good_parse_questions()
