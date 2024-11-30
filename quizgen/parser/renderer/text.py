import re

import quizgen.parser.renderer.base

class QuizgenRendererText(quizgen.parser.renderer.base.QuizgenRendererBase):
    def _text(self, node, context):
        return _clean_text(node.text())

    def _softbreak(self, node, context):
        return "\n"

    def _hardbreak(self, node, context):
        return "\n\n"

    def _em(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _strong(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _fence(self, node, context):
        return node.text().strip()

    def _code_block(self, node, context):
        return self._fence(node, context)

    def _code_inline(self, node, context):
        return node.text().strip()

    def _math_block(self, node, context):
        return node.text().strip()

    def _math_inline(self, node, context):
        return node.text().strip()

    def _image(self, node, context):
        return ''

    def _link(self, node, context):
        return node.get('href', '')

    def _placeholder(self, node, context):
        return _clean_text(node.text())

    def _table(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _thead(self, node, context):
        return "\n".join([self._render_node(child, context) for child in node.children()])

    def _tbody(self, node, context):
        return "\n".join([self._render_node(child, context) for child in node.children()])

    def _tr(self, node, context):
        return ' '.join([self._render_node(child, context) for child in node.children()])

    def _th(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _td(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _bullet_list(self, node, context):
        return "\n".join([self._render_node(child, context) for child in node.children()])

    def _ordered_list(self, node, context):
        return "\n".join([self._render_node(child, context) for child in node.children()])

    def _list_item(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _hr(self, node, context):
        return ''

    def _heading(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _blockquote(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

def get_renderer(options):
    return QuizgenRendererText(), options

def _clean_text(text):
    return text
