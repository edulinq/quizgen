import re

import markdown_it
import mdit_py_plugins.container
import mdit_py_plugins.dollarmath

import quizgen.parser.document

_parser = None
_options = None

EXTRA_OPTIONS = [
    'table',
]

PLUGINS = [
    (mdit_py_plugins.dollarmath.dollarmath_plugin, {}),
]

# TEST - We may be able to use the containers plugin for style blocks.

def _get_parser():
    _parser = markdown_it.MarkdownIt('commonmark')

    for option in EXTRA_OPTIONS:
        _parser.enable(option)

    for (plugin, options) in PLUGINS:
        _parser.use(plugin, **options)

    _options = _parser.options

    return _parser, _options

def _clean_text(text):
    # Remove carriage returns.
    text = text.replace("\r", '')

    # Trim whitespace.
    text = text.strip();

    # TEST -- Is this necessary.
    # Replace the final newline and add one additional one (for tables).
    text += "\n\n"

    return text

# Returns (transformed text, tokens).
def _parse_text(text, base_dir):
    # Special case for empty documents.
    if (text.strip() == ''):
        return ('', [])

    text = _clean_text(text)

    parser, _ = _get_parser()

    tokens = parser.parse(text)
    tokens = _post_process(tokens)

    document = quizgen.parser.document.ParsedDocument(tokens, base_dir = base_dir)

    return (text.strip(), document)

def _post_process(tokens):
    """
    Post-process the token stream.
    This allows us to edit the AST without needing the change the parser.
    """

    tokens = _remove_html(tokens)
    tokens = _remove_empty_tokens(tokens)

    return tokens

def _remove_empty_tokens(tokens):
    """
    Remove any inline's without text or blocks without children.
    """

    # Keep looping until nothing is removed.
    while True:
        remove_indexes = []
        for i in range(len(tokens)):
            token = tokens[i]

            # Remove empty leaf content nodes.
            if ((token.type in quizgen.parser.common.CONTENT_NODES) and (token.content == '')):
                remove_indexes.append(i)

            # Check children for removal.
            if (_has_children(token)):
                child_count = len(token.children)
                token.children = _remove_empty_tokens(token.children)

                # Remove nodes that have been emptied out.
                if (len(token.children) == 0):
                    remove_indexes.append(i)

            # Check for empty containers.
            # Look for this token being the open, and the next token being the close.
            if ((i < (len(tokens) - 1)) and (token.type.endswith('_open')) and (tokens[i + 1].type.endswith('_close'))):
                next_token = tokens[i + 1]
                base_type = re.sub('_open$', '', token.type)
                next_base_type = re.sub('_close$', '', next_token.type)

                # Remove if types match and neither has any kids (close should never have kids).
                if ((base_type == next_base_type) and (not _has_children(token)) and (not _has_children(next_token))):
                    remove_indexes += [i, i + 1]

        for remove_index in sorted(list(set(remove_indexes)), reverse = True):
            tokens.pop(remove_index)

        if (len(remove_indexes) == 0):
            break

    return tokens

def _remove_html(tokens):
    """
    Remove all HTML tags.
    This will recursively descend to find all tags.
    We want to allow HTML for comments and styling, but generally remove all HTML before rendering.
    """

    remove_indexes = []
    for i in range(len(tokens)):
        token = tokens[i]

        if (token.type in ['html_block', 'html_inline']):
            remove_indexes.append(i)

        if (_has_children(token)):
            token.children = _remove_html(token.children)

    for remove_index in reversed(remove_indexes):
        tokens.pop(remove_index)

    return tokens

def _has_children(token):
    return ((token.children is not None) and (len(token.children) > 0))
