import re

import bs4

import quizgen.parser.parse
import quizgen.parser.renderer.canvas
import quizgen.parser.renderer.html
import quizgen.parser.renderer.markdown
import quizgen.parser.renderer.tex
import quizgen.parser.renderer.text

def canvas(tokens, env = {}, pretty = True, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.canvas.get_renderer(options)
    raw_html = renderer.render(tokens, options, env)

    return clean_html(raw_html, pretty = pretty)

def html(tokens, env = {}, pretty = True, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.html.get_renderer(options)
    raw_html = renderer.render(tokens, options, env)

    return clean_html(raw_html, pretty = pretty)

def md(tokens, env = {}, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.markdown.get_renderer(options)
    content = renderer.render(tokens, options, env)

    return content.strip()

def tex(tokens, env = {}, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.tex.get_renderer(options)
    content = renderer.render(tokens, options, env)

    return content.strip()

def text(tokens, env = {}, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.text.get_renderer(options)
    content = renderer.render(tokens, options, env)

    return content.strip()

def render(format, tokens, env = {}, **kwargs):
    """
    General routing render function.
    """

    render_function = globals().get(format, None)
    if (render_function is None):
        raise ValueError("Could not find render function: 'quizgen.parser.render.%s'." % (format))

    return render_function(tokens, env = env, **kwargs)

def clean_html(raw_html, pretty = True):
    document = bs4.BeautifulSoup(raw_html, 'html.parser')

    formatter = bs4.formatter.HTMLFormatter(indent = 4, entity_substitution = bs4.dammit.EntitySubstitution.substitute_xml)
    if (pretty):
        content = document.prettify(formatter = formatter)
    else:
        # Remove whitespace adjacent to tags.
        content = re.sub(r'(>)\s+|\s+(<)', r'\1\2', document.prettify(formatter = formatter))

    return content.strip()
