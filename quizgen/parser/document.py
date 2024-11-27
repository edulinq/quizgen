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

    def to_markdown(self, **kwargs):
        env = {quizgen.parser.common.CONTEXT_ENV_KEY: self._prep_context(kwargs)}
        return quizgen.parser.render.markdown(self._tokens, env = env, **kwargs)

    def to_tex(self, **kwargs):
        env = {quizgen.parser.common.CONTEXT_ENV_KEY: self._prep_context(kwargs)}
        return quizgen.parser.render.tex(self._tokens, env = env, **kwargs)

    def to_text(self, **kwargs):
        # TODO: Make more simple than markdown.
        env = {quizgen.parser.common.CONTEXT_ENV_KEY: self._prep_context(kwargs)}
        return quizgen.parser.render.markdown(self._tokens, env = env, **kwargs)

    def to_html(self, **kwargs):
        env = {quizgen.parser.common.CONTEXT_ENV_KEY: self._prep_context(kwargs)}
        return quizgen.parser.render.html(self._tokens, env = env, **kwargs)

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
        Get a represetation of this document's AST.
        """

        return quizgen.parser.ast.build(self._tokens)

    def _prep_context(self, options = {}):
        """
        Prep an immutable copy/reference to the context to be passed for rendering.
        """

        # Make a copy of the context only if we need to.
        context = self._context
        if (len(options) > 0):
            context = copy.deepcopy(context)
            context.update(options)

        return types.MappingProxyType(context)
