import markdown_it.renderer
import mdformat.renderer

import quizgen.constants
import quizgen.parser.image
import quizgen.parser.parse

# TEST - Cache renderers and options?

# TEST - HTML comments are allowed in commonmark. Will they work when we disable HTML.

# TEST - node.info shuold give fence info, which will allow for style using fences.

class QuizgenRendererHTML(markdown_it.renderer.RendererHTML):
    def image(self, tokens, idx, options, env):
        # Do custom rendering and then pass onto super.
        quizgen.parser.image.render(quizgen.constants.FORMAT_HTML, tokens, idx, options, env)
        return super().image(tokens, idx, options, env)

def html(tokens, env = {}):
    _, options = quizgen.parser.parse._get_parser()

    renderer = QuizgenRendererHTML()
    return renderer.render(tokens, options, env)

def markdown(tokens, env = {}):
    _, options = quizgen.parser.parse._get_parser()

    renderer = mdformat.renderer.MDRenderer()
    return renderer.render(tokens, options, env)
