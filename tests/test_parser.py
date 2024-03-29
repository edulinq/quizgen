import re

import quizgen.parser
import tests.base

class TestParser(tests.base.BaseTest):
    """
    Test parsing.
    Good and bad situations will be loaded below into individual test cases.
    """

    pass

def _add_good_parse_questions(test_cases):
    for (name, text, expected) in test_cases:
        clean_name = name.lower().strip().replace(' ', '_')
        clean_name = re.sub(r'\W+', '', clean_name)

        test_name = 'test_good_parse_' + clean_name
        setattr(TestParser, test_name, _get_good_parse_test(text, expected))

def _get_good_parse_test(text, expected):
    def __method(self):
        document = quizgen.parser.parse_text(text)
        result = document.to_pod(include_metadata = False)

        self.assertJSONDictEqual(expected, result)

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

# [[name, input, expected AST], ...]
_add_good_parse_questions([
    ['Single Word', 'Text', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Text'
        },
    ])],

    ['Text with Spaces', 'Foo bar', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Foo bar'
        },
    ])],

    ['Text with Implicit Newlines', '\nFoo\nbar\n', _wrap_block([
        {
            'type': 'text',
            'nodes': [{
                'type': 'normal_text',
                'text': 'Foo',
            }],
        },
        {
            'type': 'text',
            'nodes': [{
                'type': 'normal_text',
                'text': 'bar',
            }],
        },
    ])],

    ['Text with Explicit Linebreak', '\nFoo\\nbar\n', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Foo',
        },
        {
            'type': 'linebreak',
        },
        {
            'type': 'normal_text',
            'text': 'bar'
        },
    ])],

    ['Basic Italics', 'Some *italics* text.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Some '
        },
        {
            'type': 'italics_text',
            'text': 'italics'
        },
        {
            'type': 'normal_text',
            'text': ' text.'
        },
    ])],

    ['Italics with Spaces', 'Some * spaced  italics   * text.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Some '
        },
        {
            'type': 'italics_text',
            'text': ' spaced  italics   '
        },
        {
            'type': 'normal_text',
            'text': ' text.'
        },
    ])],

    ['Basic Bold', 'Some **bold** text.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Some '
        },
        {
            'type': 'bold_text',
            'text': 'bold'
        },
        {
            'type': 'normal_text',
            'text': ' text.'
        },
    ])],

    ['Bold with Spaces', 'Some ** spaced  bold   ** text.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Some '
        },
        {
            'type': 'bold_text',
            'text': ' spaced  bold   '
        },
        {
            'type': 'normal_text',
            'text': ' text.'
        },
    ])],

    ['Escaped Backslash', 'Escape \\\\ backslash.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape \\ backslash.'
        },
    ])],

    ['Escaped Asterisk', 'Escape \\* asterisk.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape * asterisk.'
        },
    ])],

    ['Escaped Pipe', 'Escape \\| pipe.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape | pipe.'
        },
    ])],

    ['Escaped Backtick', 'Escape \\` backtick.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape ` backtick.'
        },
    ])],

    ['Escaped Dash', 'Escape \\- dash.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape - dash.'
        },
    ])],

    ['Escaped Bang', 'Escape \\! bang.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape ! bang.'
        },
    ])],

    ['Escaped Open Bracket', 'Escape \\[ open bracket.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape [ open bracket.'
        },
    ])],

    ['Escaped Open Brace', 'Escape \\{ open brace.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape { open brace.'
        },
    ])],

    ['Escaped Slash', 'Escape \\/ slash.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape / slash.'
        },
    ])],

    ['Basic Inline Code', '`inline_code();`', _wrap_text_nodes([
        {
            'type': 'code',
            'inline': True,
            'text': 'inline_code();'
        },
    ])],

    ['Mid-Text Inline Code', 'Inline `code()`.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Inline '
        },
        {
            'type': 'code',
            'inline': True,
            'text': 'code()'
        },
        {
            'type': 'normal_text',
            'text': '.'
        },
    ])],

    ['Inline Code with Escapes', '`inline_code("\\`");`', _wrap_text_nodes([
        {
            'type': 'code',
            'inline': True,
            'text': 'inline_code("`");'
        },
    ])],

    ['Basic Code Block', '```code_block()```', _wrap_block([
        {
            'type': 'code',
            'inline': False,
            'text': 'code_block()'
        },
    ])],

    ['Code Block with Inner Whitespace', '``` code_block() ```', _wrap_block([
        {
            'type': 'code',
            'inline': False,
            'text': ' code_block() '
        },
    ])],

    ['Code Block with Inner Newlines', '```\ncode_block()\n```', _wrap_block([
        {
            'type': 'code',
            'inline': False,
            'text': 'code_block()'
        },
    ])],

    ['Code Block with Unescaped Escape Characters', '```foo(1, \'-2\')\nbar("|", x*);```', _wrap_block([
        {
            'type': 'code',
            'inline': False,
            'text': 'foo(1, \'-2\')\nbar("|", x*);'
        },
    ])],

    ['Basic Inline Equation', '$ f(x) = x_i + x^2 \\alpha $', _wrap_text_nodes([
        {
            'type': 'equation',
            'inline': True,
            'text': 'f(x) = x_i + x^2 \\alpha'
        },
    ])],

    ['Inline Equation without Whitespace', 'Inline $\\text{equation}$.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Inline '
        },
        {
            'type': 'equation',
            'inline': True,
            'text': '\\text{equation}'
        },
        {
            'type': 'normal_text',
            'text': '.'
        },
    ])],

    ['Inline Equation with Dollar Sign', '$f(\\$a)$', _wrap_text_nodes([
        {
            'type': 'equation',
            'inline': True,
            'text': 'f($a)'
        },
    ])],

    ['Basic Equation Block', '$$equation + block$$', _wrap_block([
        {
            'type': 'equation',
            'inline': False,
            'text': 'equation + block'
        },
    ])],

    ['Equation Block with Unescaped Escape Characters', '$$ equation + - * / block() $$', _wrap_block([
        {
            'type': 'equation',
            'inline': False,
            'text': 'equation + - * / block()'
        },
    ])],

    ['Equation Block with Terminal Newlines', '$$\nf(x)\n$$', _wrap_block([
        {
            'type': 'equation',
            'inline': False,
            'text': 'f(x)'
        },
    ])],

    ['Equation Block with Inner Newlines', '$$ f(x)\ng(x) $$', _wrap_block([
        {
            'type': 'equation',
            'inline': False,
            'text': 'f(x)\ng(x)'
        },
    ])],

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
