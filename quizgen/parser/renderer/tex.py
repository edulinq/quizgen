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

class QuizgenRendererTex(markdown_it.renderer.RendererProtocol):
    def render(self, tokens, options, env):
        context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})

        # Work with an AST instead of tokens.
        ast = quizgen.parser.ast.build(tokens)

        # TEST
        print(json.dumps(ast, indent = 4))

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

        return "\n".join(content)

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

def get_renderer(options):
    return QuizgenRendererTex(), options

def tex_escape(text):
    """
    Prepare normal text for tex.
    """

    for key, value in TEX_REPLACEMENTS.items():
        text = text.replace(key, value)

    return text
