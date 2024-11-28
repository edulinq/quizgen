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
        quizgen.parser.image.update_token_html(tokens, idx, options, env)
        return super().image(tokens, idx, options, env)

    def container_block_open(self, tokens, idx, options, env):
        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})

        # Add on a specific class.
        tokens[idx].attrJoin('class', 'qg-block')

        # Pull any style attatched to this block and put it in a copy of the context.
        context, full_style, block_style = quizgen.parser.common.handle_block_style(tokens[idx].meta, context)
        env[quizgen.parser.common.CONTEXT_ENV_KEY] = context

        # Attatch style based on if we are the root block.
        # If root use all style, otherwise just use the style for this block.
        active_style = block_style
        if (tokens[idx].meta.get(quizgen.parser.common.TOKEN_META_KEY_ROOT, False)):
            active_style = full_style

        style_string = quizgen.parser.style.compute_html_style_string(active_style)
        if (style_string != ''):
            tokens[idx].attrSet('style', style_string)

        # Send to super for further rendering.
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
