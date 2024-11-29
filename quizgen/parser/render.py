import re

import bs4

import quizgen.parser.parse
import quizgen.parser.renderer.html
import quizgen.parser.renderer.markdown
import quizgen.parser.renderer.tex

def html(tokens, env = {}, pretty = True, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.html.get_renderer(options)
    raw_html = renderer.render(tokens, options, env)

    # Clean up the HTML we output.
    document = bs4.BeautifulSoup(raw_html, 'html.parser')

    if (pretty):
        content = document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))
    else:
        # Remove whitespace adjacent to tags.
        content = re.sub(r'(>)\s+|\s+(<)', r'\1\2', document.prettify())

    return content.strip()

def markdown(tokens, env = {}, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.markdown.get_renderer(options)
    content = renderer.render(tokens, options, env)

    return content.strip()

def tex(tokens, env = {}, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.tex.get_renderer(options)
    content = renderer.render(tokens, options, env)

    return content.strip()
