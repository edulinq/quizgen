import re

import quizgen.parser.renderer.html

# TEST - Canvas (html) images require special handling.

class QuizgenRendererCanvas(quizgen.parser.renderer.html.QuizgenRendererHTML):
    """
    Canvas generally uses HTML, but has some special cases.
    """

    def placeholder(self, tokens, idx, options, env):
        # Canvas placeholders cannot have spaces.
        text = tokens[idx].content.strip()
        text = re.sub(r'\s+', ' ', text)
        text = text.replace(' ', '_')

        return "[%s]" % (text)

def get_renderer(options):
    return QuizgenRendererCanvas(), options
