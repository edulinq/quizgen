import unittest

import quizgen.parser

class TestParser(unittest.TestCase):
    def test_cases(self):
        for i in range(len(TEST_CASES)):
            text, expected = TEST_CASES[i]

            with self.subTest(index = i, text = text):
                document = quizgen.parser.parse_text(text)
                result = document.to_pod(include_metadata = False)
                self.assertDictEqual(result, expected)

# Wrap a pod parser node in a block.
def _wrap_block(node):
    return {
        'type': 'document',
        'nodes': [
            {
                'type': 'block',
                'nodes': [node],
            },
        ],
    }

# Wrap text nodes in a text block.
def _wrap_text_nodes(nodes):
    return _wrap_block({
        'type': 'text',
        'nodes': nodes,
    })

TEST_CASES = [
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
]
