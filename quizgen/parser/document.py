import markdown_it

import json

import quizgen.constants
import quizgen.parser.render

BASE_DIR_KEY = 'base_dir'
CONTENT_NODES = {
    'code_inline',
    'fence',
    'text',
    'text_special',
}

class ParsedDocument(object):
    def __init__(self, tokens, base_dir = '.'):
        self._tokens = tokens
        self._context = {
            BASE_DIR_KEY: base_dir,
        }

    def set_context_value(self, key, value):
        self._context[key] = value

    def to_markdown(self, **kwargs):
        # TEST -- Existed for all to_*() methods. Used when dealing with Canvas images.
        # context = copy.deepcopy(self._context)
        # context.update(kwargs)

        return quizgen.parser.render.markdown(self._tokens)

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError('to_tex()')

    def to_text(self, **kwargs):
        # TODO: Make more simple than markdown.
        return quizgen.parser.render.markdown(self._tokens)

    def to_html(self, **kwargs):
        return quizgen.parser.render.html(self._tokens)

    def to_pod(self, include_metadata = True, **kwargs):
        data = {
            'type': 'document',
            'ast': self.get_ast(),
        }

        if (include_metadata):
            data["context"] = self._context

        return data

    def collect_file_paths(self, base_dir):
        # TEST
        raise NotImplementedError('collect_file_paths()')

    def trim(self, left = True, right = True):
        # TEST
        raise NotImplementedError('trim()')

    def is_empty(self):
        return (len(self._tokens) == 0)

    def to_json(self, indent = 4, sort_keys = True, **kwargs):
        return json.dumps(self.to_pod(**kwargs), indent = indent, sort_keys = sort_keys)

    def to_format(self, format, **kwargs):
        if (format == quizgen.constants.FORMAT_HTML):
            return self.to_html(**kwargs)
        elif (format == quizgen.constants.FORMAT_JSON):
            return self.to_json(**kwargs)
        elif (format == quizgen.constants.FORMAT_MD):
            return self.to_markdown(**kwargs)
        elif (format == quizgen.constants.FORMAT_TEX):
            return self.to_tex(**kwargs)
        elif (format == quizgen.constants.FORMAT_TEXT):
            return self.to_text(**kwargs)
        else:
            raise ValueError(f"Unknown format '{format}'.")

    def get_ast(self):
        """
        Get an approximate represetation of this document's AST.
        """

        tree = markdown_it.tree.SyntaxTreeNode(self._tokens)
        return _walk_ast(tree)

def _walk_ast(node):
    result = {
        'type': node.type,
    }

    if (node.type in CONTENT_NODES):
        result['text'] = node.content

    if (len(node.children) > 0):
        result['children'] = [_walk_ast(child) for child in node.children]

    return result
