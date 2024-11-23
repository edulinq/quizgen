import markdown_it.renderer
import mdformat.renderer

import quizgen.parser.parse

# TEST - Cache renderers and options?

def html(tokens, env = {}):
    _, options = quizgen.parser.parse._get_parser()

    renderer = markdown_it.renderer.RendererHTML()
    return renderer.render(tokens, options, env)

def markdown(tokens, env = {}):
    _, options = quizgen.parser.parse._get_parser()

    renderer = mdformat.renderer.MDRenderer()
    return renderer.render(tokens, options, env)
