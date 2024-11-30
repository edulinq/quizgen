import copy
import json
import types

import quizgen.constants
import quizgen.parser.ast
import quizgen.parser.render
import quizgen.parser.common

class ParsedDocument(object):
    def __init__(self, tokens, base_dir = '.'):
        self._tokens = tokens
        self._context = {
            quizgen.parser.common.BASE_DIR_KEY: base_dir,
        }

    def set_context_value(self, key, value):
        self._context[key] = value

    def to_canvas(self, **kwargs):
        return self._render(quizgen.constants.FORMAT_CANVAS, **kwargs)

    def to_md(self, **kwargs):
        return self._render(quizgen.constants.FORMAT_MD, **kwargs)

    def to_tex(self, **kwargs):
        return self._render(quizgen.constants.FORMAT_TEX, **kwargs)

    def to_text(self, **kwargs):
        return self._render(quizgen.constants.FORMAT_TEXT, **kwargs)

    def to_html(self, **kwargs):
        return self._render(quizgen.constants.FORMAT_HTML, **kwargs)

    def _render(self, format, **kwargs):
        context = quizgen.parser.common.prep_context(self._context, options = kwargs)
        env = {quizgen.parser.common.CONTEXT_ENV_KEY: context}
        return quizgen.parser.render.render(format, self._tokens, env = env, **kwargs)

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
        formatter = getattr(self, 'to_' + format)
        if (formatter is None):
            raise ValueError(f"Unknown format '{format}'.")

        return formatter(**kwargs)

    def get_ast(self):
        """
        Get a represetation of this document's AST.
        """

        return quizgen.parser.ast.build(self._tokens)
