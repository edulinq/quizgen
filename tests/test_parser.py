import quizgen.parser
import tests.base

class TestParser(tests.base.BaseTest):
    def test_good_cases(self):
        for i in range(len(GOOD_TEST_CASES)):
            text, expected = GOOD_TEST_CASES[i]

            with self.subTest(index = i, text = text):
                document = quizgen.parser.parse_text(text)
                result = document.to_pod(include_metadata = False)

                self.assertJSONDictEqual(expected, result)

    def test_bad_cases(self):
        for i in range(len(BAD_TEST_CASES)):
            text = BAD_TEST_CASES[i]

            with self.subTest(index = i, text = text):
                try:
                    quizgen.parser.parse_text(text)
                    self.fail("Failed to raise an exception.")
                except Exception:
                    # Expected.
                    pass

# Wrap a pod parser node in a block.
def _wrap_block(nodes):
    return {
        'type': 'document',
        'nodes': [
            {
                'type': 'block',
                'nodes': nodes,
            },
        ],
    }

# Wrap text nodes in a text block.
def _wrap_text_nodes(nodes):
    return _wrap_block([{
        'type': 'text',
        'nodes': nodes,
    }])

GOOD_TEST_CASES = [
    ['Text', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Text'
        },
    ])],

    ['Foo bar', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Foo bar'
        },
    ])],

    ['\nFoo\nbar\n', _wrap_block([
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

    ['\nFoo\\nbar\n', _wrap_text_nodes([
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

    ['Some *italics* text.', _wrap_text_nodes([
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

    ['Some * spaced  italics   * text.', _wrap_text_nodes([
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

    ['Some **bold** text.', _wrap_text_nodes([
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

    ['Some ** spaced  bold   ** text.', _wrap_text_nodes([
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

    ['Escape \\\\ backslash.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape \\ backslash.'
        },
    ])],

    ['Escape \\* asterisk.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape * asterisk.'
        },
    ])],

    ['Escape \\| pipe.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape | pipe.'
        },
    ])],

    ['Escape \\` backtick.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape ` backtick.'
        },
    ])],

    ['Escape \\- dash.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape - dash.'
        },
    ])],

    ['Escape \\! bang.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape ! bang.'
        },
    ])],

    ['Escape \\[ open bracket.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape [ open bracket.'
        },
    ])],

    ['Escape \\/ slash.', _wrap_text_nodes([
        {
            'type': 'normal_text',
            'text': 'Escape / slash.'
        },
    ])],

    ['`inline_code();`', _wrap_text_nodes([
        {
            'type': 'code',
            'inline': True,
            'text': 'inline_code();'
        },
    ])],

    ['Inline `code()`.', _wrap_text_nodes([
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

    ['`inline_code("\\`");`', _wrap_text_nodes([
        {
            'type': 'code',
            'inline': True,
            'text': 'inline_code("`");'
        },
    ])],

    ['```code_block()```', _wrap_block([
        {
            'type': 'code',
            'inline': False,
            'text': 'code_block()'
        },
    ])],

    ['``` code_block() ```', _wrap_block([
        {
            'type': 'code',
            'inline': False,
            'text': ' code_block() '
        },
    ])],

    ['```\ncode_block()\n```', _wrap_block([
        {
            'type': 'code',
            'inline': False,
            'text': 'code_block()'
        },
    ])],

    ['```foo(1, \'-2\')\nbar("|", x*);```', _wrap_block([
        {
            'type': 'code',
            'inline': False,
            'text': 'foo(1, \'-2\')\nbar("|", x*);'
        },
    ])],

    ['$ f(x) = x_i + x^2 \\alpha $', _wrap_text_nodes([
        {
            'type': 'equation',
            'inline': True,
            'text': 'f(x) = x_i + x^2 \\alpha'
        },
    ])],

    ['Inline $\\text{equation}$.', _wrap_text_nodes([
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

    ['$f(\\$a)$', _wrap_text_nodes([
        {
            'type': 'equation',
            'inline': True,
            'text': 'f($a)'
        },
    ])],

    ['$$equation + block$$', _wrap_block([
        {
            'type': 'equation',
            'inline': False,
            'text': 'equation + block'
        },
    ])],

    ['$$ equation + - * / block() $$', _wrap_block([
        {
            'type': 'equation',
            'inline': False,
            'text': 'equation + - * / block()'
        },
    ])],

    ['$$\nf(x)\n$$', _wrap_block([
        {
            'type': 'equation',
            'inline': False,
            'text': 'f(x)'
        },
    ])],

    ['$$ f(x)\ng(x) $$', _wrap_block([
        {
            'type': 'equation',
            'inline': False,
            'text': 'f(x)\ng(x)'
        },
    ])],

    ['[text](url)', _wrap_text_nodes([
        {
            'type': 'link',
            'text': 'text',
            'link': 'url',
        },
    ])],

    ['![alt text](url)', _wrap_text_nodes([
        {
            'type': 'image',
            'text': 'alt text',
            'link': 'url',
        },
    ])],

    ['[text]( )', _wrap_text_nodes([
        {
            'type': 'link',
            'text': 'text',
            'link': '',
        },
    ])],

    ['[ ](url)', _wrap_text_nodes([
        {
            'type': 'link',
            'text': '',
            'link': 'url',
        },
    ])],

    ['[ some text ]( some url )', _wrap_text_nodes([
        {
            'type': 'link',
            'text': 'some text',
            'link': 'some url',
        },
    ])],

    ['[ some [\\] text ]( some (\\) url )', _wrap_text_nodes([
        {
            'type': 'link',
            'text': 'some [] text',
            'link': 'some () url',
        },
    ])],

    ['[[answerReference]]', _wrap_text_nodes([
        {
            'type': 'answer-reference',
            'text': 'answerReference',
        },
    ])],

    ['[[answer_reference]]', _wrap_text_nodes([
        {
            'type': 'answer-reference',
            'text': 'answer_reference',
        },
    ])],

    ['[[A]]', _wrap_text_nodes([
        {
            'type': 'answer-reference',
            'text': 'A',
        },
    ])],

    ['// Some comment.', _wrap_text_nodes([
        {
            'type': 'comment',
            'text': 'Some comment.'
        },
    ])],

    ['// Some // comment. \\ * | ` - ! [ / ', _wrap_text_nodes([
        {
            'type': 'comment',
            'text': 'Some // comment. \\ * | ` - ! [ /'
        },
    ])],

    ['Some // comment.', _wrap_text_nodes([
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
]

BAD_TEST_CASES = [
    '[[_]]',
    '[[1]]',
    '[[_a]]',
    '[[1a]]',
    '[[%a]]',
]
