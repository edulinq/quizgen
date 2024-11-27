import base64
import os
import re

import quizgen.constants
import quizgen.parser.common
import quizgen.parser.style

HTML_BORDER_SPEC = '1px solid black'

def render_html(tokens, idx, options, env):
    """
    We don't need to change the output content, just the styling/attributes.
    """

    token = tokens[idx]
    context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
    style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})

    if (token.type == 'table_open'):
        _table_html(token, style)
    elif (token.type == 'thead_open'):
        _thead_html(token, style)
    elif (token.type == 'th_open'):
        _cell_html(token, style)
        _th_html(token, style)
    elif (token.type == 'td_open'):
        _cell_html(token, style)

def _table_html(token, style):
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

    _join_style(token, table_style)

def _cell_html(token, style):
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

    _join_style(token, [': '.join(item) for item in cell_style.items()])

def _th_html(token, style):
    weight = 'normal'
    if (quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_HEAD_BOLD, quizgen.parser.style.DEFAULT_TABLE_HEAD_BOLD)):
        weight = 'bold'

    _join_style(token, ["font-weight: %s" % (weight)])

def _thead_html(token, style):
    if (not quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_HEAD_RULE, quizgen.parser.style.DEFAULT_TABLE_HEAD_RULE)):
        return

    _join_style(token, ["border-bottom: %s" % (HTML_BORDER_SPEC)])

def _join_style(token, rules):
    """
    Take all style rules to apply, add in any existing style, and set the style attribute.
    """

    existing_style = token.attrGet('style')
    if (existing_style is not None):
        rules = [existing_style] + rules

    style_string = '; '.join(rules)
    token.attrSet('style', style_string)
