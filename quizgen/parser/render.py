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
    return document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

def markdown(tokens, env = {}, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.markdown.get_renderer(options)
    return renderer.render(tokens, options, env)

def tex(tokens, env = {}, **kwargs):
    _, options = quizgen.parser.parse._get_parser()

    renderer, options = quizgen.parser.renderer.tex.get_renderer(options)
    return renderer.render(tokens, options, env)
