import markdown_it

import quizgen.parser.document

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

    # TEST -- Cache parser?
    parser = markdown_it.MarkdownIt('js-default')
    tokens = parser.parse(text)
    document = quizgen.parser.document.ParsedDocument(tokens, base_dir = base_dir)

    return (text.strip(), document)
