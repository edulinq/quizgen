# TEST
import json
import os
import re

import bs4

import quizgen.constants
import quizgen.parser
import tests.base

class TestParser(tests.base.BaseTest):
    """
    Test parsing.
    Good and bad situations will be loaded below into individual test cases.
    """

    @classmethod
    def setUpClass(cls):
        # Disable KaTeX for testing.
        quizgen.parser.EquationNode.katex_available = False

    @classmethod
    def tearDownClass(cls):
        quizgen.parser.EquationNode.katex_available = None

def _add_good_parse_questions():
    for path in tests.base.discover_good_document_files():
        with open(path, 'r') as file:
            documents = json.load(file)

        base_dir = os.path.dirname(path)

        for document in documents:
            text = document['text']

            for (doc_format, expected) in document['formats'].items():
                test_name = _make_name('good_parse', path, document['name'], doc_format)
                options = document.get('options', {}).get(doc_format, {})
                setattr(TestParser, test_name, _get_good_parse_test(text, doc_format, expected, base_dir, options))

def _make_name(prefix, path, name, doc_format):
    clean_name = name.lower().strip().replace(' ', '_')
    clean_name = re.sub(r'\W+', '', clean_name)

    filename = os.path.splitext(os.path.basename(path))[0]

    return "test_%s__%s__%s__%s" % (prefix, filename, clean_name, doc_format)

def _get_good_parse_test(text, doc_format, base_expected, base_dir, options):
    def __method(self):
        document = quizgen.parser.parse_text(text)
        result = document.to_format(doc_format, base_dir = base_dir, include_metadata = False)

        if (doc_format == quizgen.constants.FORMAT_JSON):
            result = json.loads(result)
            expected = {
                'type': 'document',
                'root': base_expected,
            }

            self.assertJSONDictEqual(expected, result)
        elif (doc_format == quizgen.constants.FORMAT_HTML):
            expected = f"""
                <div class='document'>
                    {base_expected}
                </div>
            """

            document = bs4.BeautifulSoup(expected, 'html.parser')
            expected = document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

            document = bs4.BeautifulSoup(result, 'html.parser')
            result = document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

            expected, result = _apply_text_options(options, expected, result)
            self.assertEqual(expected, result)
        else:
            expected = base_expected.strip()
            result = result.strip()

            expected, result = _apply_text_options(options, expected, result)
            self.assertEqual(expected, result)

    return __method

def _apply_text_options(options, a, b):
    if (options.get("ignore-whitespace", False)):
        a = re.sub(r'\s+', '', a)
        b = re.sub(r'\s+', '', b)

    return a, b

# TEST
def _add_bad_parse_questions(test_cases):
    for (name, text) in test_cases:
        clean_name = name.lower().strip().replace(' ', '_')
        clean_name = re.sub(r'\W+', '', clean_name)

        test_name = 'test_bad_parse_' + clean_name
        setattr(TestParser, test_name, _get_bad_parse_test(text))

def _get_bad_parse_test(text):
    def __method(self):
        try:
            quizgen.parser.parse_text(text)
            self.fail("Failed to raise an exception.")
        except Exception:
            # Expected.
            pass

    return __method

# Wrap a pod parser node in a block.
def _wrap_block(nodes, style = None):
    data = {
        'type': 'document',
        'root': {
            'type': 'block',
            'nodes': [
                {
                    'type': 'block',
                    'nodes': nodes,
                }
            ],
        },
    }

    if ((style is not None) and (len(style) > 0)):
        data['root']['style'] = style

    return data

# Wrap text nodes in a text block.
def _wrap_text_nodes(nodes):
    return _wrap_block([{
        'type': 'text',
        'nodes': nodes,
    }])

# TEST - Style
# TEST - Style Nest
# TEST - Style Pop
# TEST - Style

# [(name, text), ...]
_add_bad_parse_questions([
    ('Answer Reference with Only Underscore', '[[_]]'),
    ('Answer Reference with Only Number', '[[1]]'),
    ('Answer Reference Starting with Underscore', '[[_a]]'),
    ('Answer Reference Starting with Number', '[[1a]]'),
    ('Answer Reference Starting with Character', '[[%a]]'),
])

_add_good_parse_questions()
