import re

import lxml.etree

import quizgen.parser.parse
import quizgen.parser.renderer.canvas
import quizgen.parser.renderer.html
import quizgen.parser.renderer.markdown
import quizgen.parser.renderer.tex
import quizgen.parser.renderer.text

def canvas(tokens, env = {}, pretty = False, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.canvas.get_renderer(options)
    raw_html = renderer.render(tokens, options, env)

    return clean_html(raw_html, pretty = pretty)

def html(tokens, env = {}, pretty = False, **kwargs):
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

def clean_html(raw_html, pretty = False):
    """
    Clean up and standardize the HTML.
    If |pretty|, then the output will be indented properly, and extra space will be stripped (which may mess with some inline spacing).
    |pretty| should only be used when being read by a human for visual inspection.
    """

    raw_html = raw_html.strip()
    if (len(raw_html) == 0):
        return raw_html

    parser = lxml.etree.XMLParser(remove_blank_text = True)
    root = lxml.etree.fromstring(raw_html, parser)
    content = lxml.etree.tostring(root, pretty_print = pretty, encoding = 'unicode')

    return content.strip()
