import copy
import types

import markdown_it.renderer

import quizgen.constants
import quizgen.parser.common
import quizgen.parser.image
import quizgen.parser.math
import quizgen.parser.style
import quizgen.parser.table

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

    def table_open(self, tokens, idx, options, env):
        return self._table_elements(tokens, idx, options, env)

    def thead_open(self, tokens, idx, options, env):
        return self._table_elements(tokens, idx, options, env)

    def th_open(self, tokens, idx, options, env):
        return self._table_elements(tokens, idx, options, env)

    def td_open(self, tokens, idx, options, env):
        return self._table_elements(tokens, idx, options, env)

    def _table_elements(self, tokens, idx, options, env):
        # Do custom rendering and then pass onto super.
        quizgen.parser.table.render_html(tokens, idx, options, env)
        return super().renderToken(tokens, idx, options, env)

def get_renderer(options):
    return QuizgenRendererHTML(), options
