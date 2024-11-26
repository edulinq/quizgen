import copy
import types

import markdown_it.renderer
import mdformat.plugins
import mdformat.renderer

import quizgen.constants
import quizgen.parser.common
import quizgen.parser.image
import quizgen.parser.math
import quizgen.parser.parse
import quizgen.parser.style

# TEST - Cache renderers and options?

class QuizgenRendererHTML(markdown_it.renderer.RendererHTML):
    def image(self, tokens, idx, options, env):
        # Do custom rendering and then pass onto super.
        quizgen.parser.image.render(quizgen.constants.FORMAT_HTML, tokens, idx, options, env)
        return super().image(tokens, idx, options, env)

    def container_block_open(self, tokens, idx, options, env):
        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})

        # Add on a specific class and send back to super for full rendering.
        tokens[idx].attrJoin('class', 'qg-block')

        # Attatch any style specific to this block.
        block_style = tokens[idx].meta.get(quizgen.parser.common.TOKEN_META_KEY_STYLE, {})
        style_string = quizgen.parser.style.compute_html_style_string(block_style)
        if (style_string != ''):
            tokens[idx].attrSet('style', style_string)

        # Pass on any new style though the env.
        if (len(block_style) > 0):
            env_style = context.get('style', {})
            env_style.update(block_style)

            # Make a readonly copy of the updated context.
            context = copy.deepcopy(dict(context))
            context['style'] = env_style
            env[quizgen.parser.common.CONTEXT_ENV_KEY] = types.MappingProxyType(context)

        return super().renderToken(tokens, idx, options, env)

    def math_inline(self, tokens, idx, options, env):
        return quizgen.parser.math.render(quizgen.constants.FORMAT_HTML, True, tokens, idx, options, env)

    def math_block(self, tokens, idx, options, env):
        return quizgen.parser.math.render(quizgen.constants.FORMAT_HTML, False, tokens, idx, options, env)

    def placeholder(self, tokens, idx, options, env):
        return "<placeholder>%s</placeholder>" % (tokens[idx].content)

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
    def placeholder(node, context):
        return "<placeholder>%s</placeholder>" % (node.content)

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
        'placeholder': placeholder,
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
