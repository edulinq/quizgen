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

# TEST
def _add_good_parse_questions():
    for path in tests.base.discover_good_document_files():
        with open(path, 'r') as file:
            documents = json.load(file)

        for document in documents:
            text = document['text']

            for (doc_format, expected) in document['formats'].items():
                test_name = _make_name('good_parse', path, document['name'], doc_format)
                setattr(TestParser, test_name, _get_good_parse_test(text, doc_format, expected))

''' TEST
def _add_good_parse_questions(test_cases):
    for (name, text, expected) in test_cases:
        clean_name = name.lower().strip().replace(' ', '_')
        clean_name = re.sub(r'\W+', '', clean_name)

        test_name = 'test_good_parse_' + clean_name
        setattr(TestParser, test_name, _get_good_parse_test(text, expected))
'''

def _make_name(prefix, path, name, doc_format):
    clean_name = name.lower().strip().replace(' ', '_')
    clean_name = re.sub(r'\W+', '', clean_name)

    filename = os.path.splitext(os.path.basename(path))[0]

    return "test_%s__%s__%s__%s" % (prefix, filename, clean_name, doc_format)

def _get_good_parse_test(text, doc_format, base_expected):
    def __method(self):
        document = quizgen.parser.parse_text(text)
        result = document.to_format(doc_format, include_metadata = False)

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

            document = bs4.BeautifulSoup(result, 'html.parser')
            result = document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

            document = bs4.BeautifulSoup(expected, 'html.parser')
            expected = document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

            self.assertEqual(expected, result)
        else:
            result = result.strip()
            expected = base_expected.strip()

            self.assertEqual(expected, result)

    return __method

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

""" TEST
# [[name, input, expected AST], ...]
_add_good_parse_questions([

    ['Basic Link', '[text](url)', _wrap_text_nodes([
        {
            'type': 'link',
            'text': 'text',
            'link': 'url',
        },
    ])],

    ['Basic Image', '![alt text](url)', _wrap_text_nodes([
        {
            'type': 'image',
            'text': 'alt text',
            'link': 'url',
        },
    ])],

    ['Link with No URL', '[text]( )', _wrap_text_nodes([
        {
            'type': 'link',
            'text': 'text',
            'link': '',
        },
    ])],

    ['Link with No Text', '[ ](url)', _wrap_text_nodes([
        {
            'type': 'link',
            'text': '',
            'link': 'url',
        },
    ])],

    ['Link with Extra Whitesspace', '[ some text ]( some url )', _wrap_text_nodes([
        {
            'type': 'link',
            'text': 'some text',
            'link': 'some url',
        },
    ])],

    ['Link with Escaped Characters', '[ some [\\] text ]( some (\\) url )', _wrap_text_nodes([
        {
            'type': 'link',
            'text': 'some [] text',
            'link': 'some () url',
        },
    ])],

    ['Basic Answer Reference', '[[answerReference]]', _wrap_text_nodes([
        {
            'type': 'answer-reference',
            'text': 'answerReference',
        },
    ])],

    ['Answer Reference with Underscore', '[[answer_reference]]', _wrap_text_nodes([
        {
            'type': 'answer-reference',
            'text': 'answer_reference',
        },
    ])],

    ['One Character Answer Reference', '[[A]]', _wrap_text_nodes([
        {
            'type': 'answer-reference',
            'text': 'A',
        },
    ])],

    ['Basic Slash Comment', '// Some comment.', _wrap_text_nodes([
        {
            'type': 'comment',
            'text': 'Some comment.'
        },
    ])],

    ['Slash Comment with Slashes', '// Some // comment. \\ * | ` - ! [ / ', _wrap_text_nodes([
        {
            'type': 'comment',
            'text': 'Some // comment. \\ * | ` - ! [ /'
        },
    ])],

    ['Mid-Line Slash Comment', 'Some // comment.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Some '
        },
        {
            'type': 'comment',
            'text': 'comment.'
        },
    ])],

    [
        'Basic Table',
        '''
| a | b | c |
        ''',
        _wrap_block([
            {
                'type': 'table',
                'rows': [
                    {
                        'type': 'table-row',
                        'head': False,
                        'cells': [
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'normal_text',
                                        'text': 'a'
                                    },
                                ],
                            },
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'normal_text',
                                        'text': 'b'
                                    },
                                ],
                            },
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'normal_text',
                                        'text': 'c'
                                    },
                                ],
                            },
                        ]
                    },
                ],
            }
        ])
    ],

    [
        'One-Column Table Separator',
        '''
|---|
        ''',
        _wrap_block([
            {
                'type': 'table',
                'rows': [
                    {
                        'type': 'table-sep'
                    },
                ],
            }
        ])
    ],

    [
        'Two-Column Table Separator',
        '''
|---|---|
        ''',
        _wrap_block([
            {
                'type': 'table',
                'rows': [
                    {
                        'type': 'table-sep'
                    },
                ],
            }
        ])
    ],

    [
        'Table Separator with Short Dashes',
        '''
|---| |
        ''',
        _wrap_block([
            {
                'type': 'table',
                'rows': [
                    {
                        'type': 'table-sep'
                    },
                ],
            }
        ])
    ],

    [
        'Table Seperator That Doesn\' Fill Column',
        '''
|--- | |
        ''',
        _wrap_block([
            {
                'type': 'table',
                'rows': [
                    {
                        'type': 'table-sep'
                    },
                ],
            }
        ])
    ],

    [
        'Table with Differnet Text Types',
        '''
|- 1  | \-2   |         3^        |
|-----|-------|-------------------|
| *a* | **b** | `c()` and $ d() $ |
        ''',
        _wrap_block([
            {
                'type': 'table',
                'rows': [
                    {
                        'type': 'table-row',
                        'head': True,
                        'cells': [
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'normal_text',
                                        'text': '1'
                                    },
                                ],
                            },
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'normal_text',
                                        'text': '-2',
                                    },
                                ],
                            },
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'normal_text',
                                        'text': '3^'
                                    },
                                ],
                            },
                        ]
                    },
                    {
                        'type': 'table-sep'
                    },
                    {
                        'type': 'table-row',
                        'head': False,
                        'cells': [
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'italics_text',
                                        'text': 'a'
                                    },
                                ],
                            },
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'bold_text',
                                        'text': 'b'
                                    },
                                ],
                            },
                            {
                                'type': 'text',
                                'nodes': [
                                    {
                                        'type': 'code',
                                        'inline': True,
                                        'text': 'c()'
                                    },
                                    {
                                        'type': 'normal_text',
                                        'text': ' and '
                                    },
                                    {
                                        'type': 'equation',
                                        'inline': True,
                                        'text': 'd()'
                                    },
                                ],
                            },
                        ]
                    },
                ],
            }
        ])
    ],

    [
        'Root Style',
        '''
{{
    "font-size": 12
}}
        ''',
        {
            'type': 'document',
            'root': {
                'type': 'block',
                'nodes': [],
                'style': {
                    'font-size': 12,
                }
            }
        },
    ],

    [
        'Root Style Alongside Text',
        '''
Base Style

{{
    "font-size": 12
}}
        ''',
        _wrap_block(
            [{
                'type': 'text',
                'nodes': [{
                    'type': 'normal_text',
                    'text': 'Base Style',
                }],
            }],
            style = {
                'font-size': 12,
            }
        )
    ],
])
"""

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

# TEST
_add_good_parse_questions()
