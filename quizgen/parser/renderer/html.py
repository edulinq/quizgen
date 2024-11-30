import copy
import os
import re
import types

import markdown_it.renderer

import quizgen.constants
import quizgen.parser.common
import quizgen.parser.image
import quizgen.parser.math
import quizgen.parser.style

HTML_BORDER_SPEC = '1px solid black'

class QuizgenRendererHTML(markdown_it.renderer.RendererHTML):
    def image(self, tokens, idx, options, env):
        # Do custom rendering and then pass onto super.

        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})

        base_dir = context.get(quizgen.parser.common.BASE_DIR_KEY, '.')
        callback = context.get(quizgen.parser.common.CONTEXT_KEY_IMAGE_CALLBACK, None)

        src = tokens[idx].attrGet('src')
        src = quizgen.parser.image.handle_callback(callback, src, base_dir)
        tokens[idx].attrSet('src', src)

        # Set width.
        width_float = quizgen.parser.style.get_image_width(style)
        tokens[idx].attrSet('width', "%0.2f%%" % (width_float * 100.0))

        path = os.path.realpath(os.path.join(base_dir, src))
        force_raw_image_src = context.get(quizgen.parser.common.CONTEXT_KEY_FORCE_RAW_IMAGE_SRC, False)

        if (force_raw_image_src or re.match(r'^http(s)?://', src)):
            # Do not further modify the src if it is a http URL or we are explicitly directed not to.
            pass
        else:
            # Otherwise, do a base64 encoding of the image and embed it.
            mime, content = quizgen.parser.image.encode_image(path)
            tokens[idx].attrSet('src', f"data:{mime};base64,{content}")

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
        token = tokens[idx]
        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})

        table_style = [
            'border-collapse: collapse',
        ]

        if (quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_BORDER_TABLE, quizgen.parser.style.DEFAULT_TABLE_BORDER_TABLE)):
            table_style.append("border: %s" % HTML_BORDER_SPEC)
        else:
            table_style.append('border-style: hidden')

        # HTML tables require extra encouragement to align.
        text_align = quizgen.parser.style.get_alignment(style, quizgen.parser.style.KEY_TEXT_ALIGN)
        if (text_align is not None):
            table_style.append("text-align: %s" % (text_align))

        _join_html_style(token, table_style)

        return super().renderToken(tokens, idx, options, env)

    def thead_open(self, tokens, idx, options, env):
        token = tokens[idx]
        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})

        if (quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_HEAD_RULE, quizgen.parser.style.DEFAULT_TABLE_HEAD_RULE)):
            _join_html_style(token, ["border-bottom: %s" % (HTML_BORDER_SPEC)])

        return super().renderToken(tokens, idx, options, env)

    def th_open(self, tokens, idx, options, env):
        token = tokens[idx]
        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})

        self._cell_html(token, style)

        weight = 'normal'
        if (quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_HEAD_BOLD, quizgen.parser.style.DEFAULT_TABLE_HEAD_BOLD)):
            weight = 'bold'

        _join_html_style(token, ["font-weight: %s" % (weight)])

        return super().renderToken(tokens, idx, options, env)

    def td_open(self, tokens, idx, options, env):
        token = tokens[idx]
        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})

        self._cell_html(token, style)

        return super().renderToken(tokens, idx, options, env)

    def _cell_html(self, token, style):
        """
        Common cell rendering.
        """

        height = max(1.0, float(style.get(quizgen.parser.style.KEY_TABLE_CELL_HEIGHT, quizgen.parser.style.DEFAULT_TABLE_CELL_HEIGHT)))
        vertical_padding = height - 1.0

        width = max(1.0, float(style.get(quizgen.parser.style.KEY_TABLE_CELL_WIDTH, quizgen.parser.style.DEFAULT_TABLE_CELL_WIDTH)))
        horizontal_padding = width - 1.0

        cell_style = {
            'padding-top': "%0.2fem" % (vertical_padding / 2),
            'padding-bottom': "%0.2fem" % (vertical_padding / 2),
            'padding-left': "%0.2fem" % (horizontal_padding / 2),
            'padding-right': "%0.2fem" % (horizontal_padding / 2),
        }

        if (quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_BORDER_CELLS, quizgen.parser.style.DEFAULT_TABLE_BORDER_CELLS)):
            cell_style['border'] = "%s" % (HTML_BORDER_SPEC)

        _join_html_style(token, [': '.join(item) for item in cell_style.items()])

def get_renderer(options):
    return QuizgenRendererHTML(), options

def _join_html_style(token, rules):
    """
    Take all style rules to apply, add in any existing style, and set the style attribute.
    """

    existing_style = token.attrGet('style')
    if (existing_style is not None):
        rules = [existing_style] + rules

    style_string = '; '.join(rules)
    token.attrSet('style', style_string)
