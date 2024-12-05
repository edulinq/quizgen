import quizgen.constants
import quizgen.katex
import quizgen.parser.common

_katex_available = None

def render(format, inline, tokens, idx, options, env):
    context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
    text = tokens[idx].content

    if (format == quizgen.constants.FORMAT_HTML):
        return _render_html(text, inline, context)
    elif (format == quizgen.constants.FORMAT_MD):
        return _render_md(text, inline, context)
    elif (format == quizgen.constants.FORMAT_TEX):
        return _render_tex(text, inline, context)
    elif (format == quizgen.constants.FORMAT_TEXT):
        return _render_md(text, inline, context)
    else:
        raise ValueError(f"Unknown format '{format}'.")

def _render_tex(text, inline, context):
    text = text.replace('$', r'\$')

    if (inline):
        text = text.strip()
        return f"$ {text} $"

    return f"$$\n{text}\n$$"

def _render_html(text, inline, context):
    global _katex_available

    if (_katex_available is None):
        _katex_available = quizgen.katex.is_available()

    if (inline):
        text = text.strip()

    content = f"<code>{text}</code>"
    if (_katex_available):
        content = quizgen.katex.to_html(text)

    element = 'span'
    attributes = 'style="margin-left: 0.25em; margin-right: 0.25em"'
    if (not inline):
        element = 'p'
        attributes = 'style="margin-top: 0"'

    return f"<{element} {attributes}>{content}</{element}>"

def _render_md(text, inline, context):
    if (inline):
        text = text.strip()
        return f"$ {text} $"

    return f"$$\n{text}\n$$"
