import json
import logging
import os

import markdown_it.renderer

import quizgen.parser.ast
import quizgen.parser.common
import quizgen.parser.image
import quizgen.parser.style

TEX_REPLACEMENTS = {
    # Specially handle braces and slashes to avoid clobbering other replacements.
    '{': 'ZZZzzz  OPEN BRACE REPLACEMENT  zzzZZZ',
    '}': 'ZZZzzz  CLOSE BRACE REPLACEMENT  zzzZZZ',
    '\\': 'ZZZzzz  BACKSLASH REPLACEMENT  zzzZZZ',

    '|': '\\textbar{}',
    '$': '\\$',
    '#': '\\#',
    '%': '\\%',
    '^': '\\^',
    '_': '\\_',
    'π': '$\\pi$',
    '`': '\\`{}',

    'ZZZzzz  OPEN BRACE REPLACEMENT  zzzZZZ': '\\{',
    'ZZZzzz  CLOSE BRACE REPLACEMENT  zzzZZZ': '\\}',
    'ZZZzzz  BACKSLASH REPLACEMENT  zzzZZZ': '\\textbackslash{}',
}

VERB_CHARACTERS = ['|', '!', '@', '#', '$', '^', '&', '-', '_', '=', '+']

TEX_TEXT_TABLE_ALIGNMENT = {
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_LEFT: 'l',
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_CENTER: 'c',
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_RIGHT: 'r',
}

class QuizgenRendererTex(markdown_it.renderer.RendererProtocol):
    def render(self, tokens, options, env):
        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})

        # Work with an AST instead of tokens.
        ast = quizgen.parser.ast.build(tokens)

        return self._render_node(ast, context)

    def _render_node(self, node, context):
        """
        Route rendering to a the method '_<type>(self, node, context)', e.g.: '_image'.
        """

        method_name = '_' + node.type()
        method = getattr(self, method_name, None)
        if (method is None):
            raise TypeError("Could not find TeX render method: '%s'." % (method_name))

        return method(node, context)

    def _root(self, node, context):
        return "\n\n".join([self._render_node(child, context) for child in node.children()])

    def _container_block(self, node, context):
        # Pull any style attatched to this block and put it in a copy of the context.
        context, full_style, block_style = quizgen.parser.common.handle_block_style(node, context)

        # Compute fixes using different styles depending on if this block is root.
        # If we are root, then we need to use all style.
        # If we are not root, then earlier blocks would have already applied other style,
        # and we only need the block style.
        active_style = block_style
        if (node.get(quizgen.parser.common.TOKEN_META_KEY_ROOT, False)):
            active_style = full_style

        prefixes, suffixes = quizgen.parser.style.compute_tex_fixes(active_style)
        child_content = [self._render_node(child, context) for child in node.children()]

        content = prefixes + child_content + list(reversed(suffixes))

        return "\n\n".join(content)

    def _paragraph(self, node, context):
        return "\n".join([self._render_node(child, context) for child in node.children()])

    def _inline(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _text(self, node, context):
        return tex_escape(node.text())

    def _softbreak(self, node, context):
        return "\n"

    def _hardbreak(self, node, context):
        return ' \\newline\n'

    def _em(self, node, context):
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return r"\textit{%s}" % (content)

    def _strong(self, node, context):
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return r"\textbf{%s}" % (content)

    def _fence(self, node, context):
        return "\\begin{lstlisting}\n%s\n\\end{lstlisting}" % node.text().rstrip()

    def _code_inline(self, node, context):
        text = node.text()

        delim = None
        for char in VERB_CHARACTERS:
            if (char not in text):
                delim = char
                break

        if (delim is None):
            raise ValueError("Could not find a delimiter to use with TeX's `\verb'.")

        return r"\verb%s%s%s" % (delim, text, delim)

    def _math_block(self, node, context):
        text = node.text().strip()
        return f"$$\n{text}\n$$"

    def _math_inline(self, node, context):
        text = node.text().strip()
        return f"$ {text} $"

    def _image(self, node, context):
        style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})
        base_dir = context.get(quizgen.parser.common.BASE_DIR_KEY, '.')
        callback = context.get(quizgen.parser.common.CONTEXT_KEY_IMAGE_CALLBACK, None)

        src = node.get('src', '')
        src = quizgen.parser.image.handle_callback(callback, src, base_dir)

        width_float = quizgen.parser.style.get_image_width(style)
        path = os.path.realpath(os.path.join(base_dir, src))

        return r"\includegraphics[width=%0.2f\textwidth]{%s}" % (width_float, src)

    def _link(self, node, context):
        text = ''.join([self._render_node(child, context) for child in node.children()]).strip()
        url = node.get('href', '')

        if (len(text) == 0):
            return r"\url{%s}" % (url)

        return r"\href{%s}{%s}" % (url, text)

    def _placeholder(self, node, context):
        text = tex_escape(node.text())
        return r"\textsc{<%s>}" % (text)

    def _table(self, node, context):
        style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})

        border_table = quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_BORDER_TABLE, quizgen.parser.style.DEFAULT_TABLE_BORDER_TABLE)
        border_cells = quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_BORDER_CELLS, quizgen.parser.style.DEFAULT_TABLE_BORDER_CELLS)
        default_alignment = quizgen.parser.style.get_alignment(style, quizgen.parser.style.KEY_TEXT_ALIGN, default_value = quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_CENTER)

        column_infos = _discover_column_info(node)

        column_join = ''
        if (border_cells):
            column_join = '|'

        # Build column specifiers.
        column_specifiers = []
        for column_info in column_infos:
            raw_alignment = column_info.get('text-align', default_alignment)
            column_specifiers.append(TEX_TEXT_TABLE_ALIGNMENT[raw_alignment])
        column_spec = column_join.join(column_specifiers)

        if (border_table):
            column_spec = '|' + column_spec + '|'

        lines = [
            r'\begin{tabular}{ ' + column_spec + ' }',
        ]

        if (border_table):
            lines.append(r'\hline')

        lines.append("\n".join([self._render_node(child, context) for child in node.children()]))

        if (border_table):
            lines.append(r'\hline')

        lines += [
            r'\end{tabular}',
        ]

        lines = _apply_tex_table_style(style, lines)

        return "\n".join(lines)

    def _thead(self, node, context):
        style = context.get(quizgen.parser.common.CONTEXT_KEY_STYLE, {})
        head_rule = quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_HEAD_RULE, quizgen.parser.style.DEFAULT_TABLE_HEAD_RULE)

        content = "\n".join([self._render_node(child, context) for child in node.children()])

        if (head_rule):
            content += '\n\\hline'

        return content

    def _tbody(self, node, context):
        content = "\n".join([self._render_node(child, context) for child in node.children()])
        return content

    def _tr(self, node, context):
        content = ' & '.join([self._render_node(child, context) for child in node.children()])
        return content + ' \\\\'

    def _th(self, node, context):
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return content

    def _td(self, node, context):
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return content

    def _bullet_list(self, node, context):
        items = '\n'.join([self._render_node(child, context) for child in node.children()])
        return "\\begin{itemize}\n" + items + "\n\\end{itemize}"

    def _ordered_list(self, node, context):
        items = '\n'.join([self._render_node(child, context) for child in node.children()])
        return "\\begin{enumerate}\n" + items + "\n\\end{enumerate}"

    def _list_item(self, node, context):
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return "    \\item " + content

def get_renderer(options):
    return QuizgenRendererTex(), options

def tex_escape(text):
    """
    Prepare normal text for tex.
    """

    for key, value in TEX_REPLACEMENTS.items():
        text = text.replace(key, value)

    return text

def _apply_tex_table_style(style, lines):
    # Height
    height = max(1.0, float(style.get(quizgen.parser.style.KEY_TABLE_CELL_HEIGHT, quizgen.parser.style.DEFAULT_TABLE_CELL_HEIGHT)))
    prefix = [
        r'\begingroup',
        r'\renewcommand{\arraystretch}{%0.2f}' % (height),
    ]
    lines = prefix + lines
    lines.append(r'\endgroup')

    # Width
    width = max(1.0, float(style.get(quizgen.parser.style.KEY_TABLE_CELL_WIDTH, quizgen.parser.style.DEFAULT_TABLE_CELL_WIDTH)))
    prefix = [
        r'\begingroup',
        r'\setlength{\tabcolsep}{%0.2fem}' % (width),
    ]
    lines = prefix + lines
    lines.append(r'\endgroup')

    return lines

def _discover_column_info(node, info = None):
    """
    Descend into a table to figure out how many columns there are and if a column has alignment information.
    We will not make assumptions about symmetric rows or existence of headers.
    The largest row will determine width, and the last instance of styling information in a column will determine alignment.
    """

    if (info is None):
        info = []

    type = node.type()
    if (type not in {'table', 'thead', 'tbody', 'tr', 'td', 'th'}):
        return info

    children = node.children()

    if (type in {'table', 'thead', 'tbody'}):
        for child in children:
            info = _discover_column_info(child, info = info)
        return info

    if (type == 'tr'):
        for i in range(len(children)):
            if (i >= len(info)):
                info.append({})

            info[i] = _discover_column_info_cells(children[i], style = info[i])

        return info

    logging.warning("Unexpected table node type '%s'." % (type))
    return info

def _discover_column_info_cells(node, style = {}):
    type = node.type()
    if (type not in {'td', 'th'}):
        return style

    raw_style = node.get('style', '').strip()
    if (len(raw_style) == 0):
        return style

    rules = [part.strip() for part in raw_style.split(';')]
    for raw_rule in rules:
        key, value = [part.strip() for part in raw_rule.split(':', maxsplit = 1)]
        style[key] = value

    return style