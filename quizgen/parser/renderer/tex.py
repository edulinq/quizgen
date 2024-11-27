import json

import markdown_it.renderer

# TEST
import quizgen.constants
import quizgen.parser.ast
import quizgen.parser.common
import quizgen.parser.image
import quizgen.parser.math
import quizgen.parser.renderer.html
import quizgen.parser.renderer.markdown
import quizgen.parser.renderer.tex
import quizgen.parser.style
import quizgen.parser.table

class QuizgenRendererTex(markdown_it.renderer.RendererProtocol):
    def render(self, tokens, options, env):
        # TEST
        print('TEST - TeX')

        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})

        # Work with an AST instead of tokens.
        ast = quizgen.parser.ast.build(tokens)

        return self._render(ast, context)

    def _render(self, node, context):
        # TEST
        print(json.dumps(node, indent = 4))

        return "TEST"

def get_renderer(options):
    return QuizgenRendererTex(), options
