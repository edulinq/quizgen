import markdown_it.renderer
import mdformat.plugins
import mdformat.renderer

import quizgen.constants
import quizgen.parser.common
import quizgen.parser.image
import quizgen.parser.math
import quizgen.parser.parse

# TEST - Cache renderers and options?

# TEST - node.info shuold give fence info, which will allow for style using fences.

class QuizgenRendererHTML(markdown_it.renderer.RendererHTML):
    def image(self, tokens, idx, options, env):
        # Do custom rendering and then pass onto super.
        quizgen.parser.image.render(quizgen.constants.FORMAT_HTML, tokens, idx, options, env)
        return super().image(tokens, idx, options, env)

    def container_block_open(self, tokens, idx, options, env):
        # Add on a specific class and send back to super for full rendering.
        tokens[idx].attrJoin('class', 'qg-block')
        return super().renderToken(tokens, idx, options, env)

    def math_inline(self, tokens, idx, options, env):
        return quizgen.parser.math.render(quizgen.constants.FORMAT_HTML, True, tokens, idx, options, env)

    def math_block(self, tokens, idx, options, env):
        return quizgen.parser.math.render(quizgen.constants.FORMAT_HTML, False, tokens, idx, options, env)

class QuizgenMDformatExtension(mdformat.plugins.ParserExtensionInterface):
    CHANGES_AST = False
    POSTPROCESSORS = {}

    @staticmethod
    def math_inline(node, context):
        qg_context = context.env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
        return quizgen.parser.math._render_md(node.content, True, qg_context)

    @staticmethod
    def math_block(node, context):
        qg_context = context.env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
        return quizgen.parser.math._render_md(node.content, False, qg_context)

    @staticmethod
    def container_block(node, context):
        # We can ignore blocks when outputting markdown (since it is non-standard).
        # Just render the child node (there should only be one).
        if ((node.children is None) or (len(node.children) == 0)):
            return ''

        parts = []
        for child in node.children:
            parts.append(child.render(context))

        return "\n\n".join(parts)

    RENDERERS = {
        'container_block': container_block,
        'math_block': math_block,
        'math_inline': math_inline,
    }

def html(tokens, env = {}):
    _, options = quizgen.parser.parse._get_parser()

    renderer = QuizgenRendererHTML()
    return renderer.render(tokens, options, env)

def markdown(tokens, env = {}):
    _, options = quizgen.parser.parse._get_parser()

    extensions = options.get('parser_extension', [])
    extensions += [
        mdformat.plugins.PARSER_EXTENSIONS['tables'],
        QuizgenMDformatExtension(),
    ]
    options['parser_extension'] = extensions

    renderer = mdformat.renderer.MDRenderer()
    return renderer.render(tokens, options, env)
