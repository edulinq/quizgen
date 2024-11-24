import markdown_it

import quizgen.parser.document

_parser = None
_options = None

EXTRA_ENABLES = [
    'table',
]

def _get_parser():
    _parser = markdown_it.MarkdownIt('commonmark').enable(EXTRA_ENABLES)
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
    tokens = _modify_tokens(tokens)

    document = quizgen.parser.document.ParsedDocument(tokens, base_dir = base_dir)

    return (text.strip(), document)

def _modify_tokens(tokens):
    """
    Modify the token's post-parse.
    This allows us to edit the AST without needing the change the parser.
    """

    tokens = _remove_html(tokens)

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

        if ((token.children is not None) and (len(token.children) > 0)):
            _remove_html(token.children)

    for remove_index in reversed(remove_indexes):
        tokens.pop(remove_index)

    return tokens
