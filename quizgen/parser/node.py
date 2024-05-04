"""
The base class for AST nodes and a place for simpler AST nodes to live.
"""

import abc
import copy
import json

import quizgen.parser.style

FLEXBOX_ALIGNMENT = {
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_LEFT: 'flex-start',
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_CENTER: 'center',
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_RIGHT: 'flex-end',
}

TEX_BLOCK_ALIGNMENT = {
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_LEFT: 'flushleft',
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_CENTER: 'center',
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_RIGHT: 'flushright',
}

class ParseNode(abc.ABC):
    @abc.abstractmethod
    def to_markdown(self, **kwargs):
        pass

    @abc.abstractmethod
    def to_tex(self, **kwargs):
        pass

    @abc.abstractmethod
    def to_text(self, **kwargs):
        pass

    @abc.abstractmethod
    def to_html(self, **kwargs):
        pass

    @abc.abstractmethod
    def to_pod(self, **kwargs):
        """
        Get a "Plain Old Data" representation of the node."
        This representation should be convertable to JSON."
        """

        pass

    def collect_file_paths(self, base_dir):
        return []

    def trim(self, left = True, right = True):
        pass

    def is_empty(self):
        return False

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

class DocumentNode(ParseNode):
    def __init__(self, nodes):
        self._root = BlockNode(nodes)
        self._context = {}

    def set_context_value(self, key, value):
        self._context[key] = value

    def set_base_dir(self, base_dir):
        self.set_context_value("base_dir", base_dir)

    def to_markdown(self, **kwargs):
        context = copy.deepcopy(self._context)
        context.update(kwargs)

        return self._root.to_markdown(**context)

    def to_text(self, **kwargs):
        context = copy.deepcopy(self._context)
        context.update(kwargs)

        return self._root.to_text(**context)

    def to_tex(self, **kwargs):
        context = copy.deepcopy(self._context)
        context.update(kwargs)

        return self._root.to_tex(**context)

    def to_html(self, **kwargs):
        context = copy.deepcopy(self._context)
        context.update(kwargs)

        content = self._root.to_html(**context)
        content = f"<div class='document'>\n{content}\n</div>"

        return content

    def to_pod(self, include_metadata = True, **kwargs):
        data = {
            "type": 'document',
            "root": self._root.to_pod(include_metadata = include_metadata),
        }

        if (include_metadata):
            data["context"] = self._context

        return data

    def collect_file_paths(self, base_dir):
        return self._root.collect_file_paths(base_dir)

class BlockNode(ParseNode):
    def __init__(self, nodes, style = {}):
        self._nodes = []
        self._style = style.copy()

        for node in nodes:
            if ((node is None) or node.is_empty()):
                continue

            if (isinstance(node, BlockNode) and node.is_liftable()):
                # Lift the child (absorb it).
                self._nodes += node._nodes
            elif (isinstance(node, StyleNode)):
                # Style nodes don't have any visible content, just style.
                self._style.update(node.to_pod())
            else:
                self._nodes.append(node)

    def to_markdown(self, style = {}, **kwargs):
        if (len(self._nodes) == 0):
            return ''

        full_style = copy.deepcopy(style)
        full_style.update(self._style)

        return "\n".join([node.to_markdown(style = full_style, **kwargs) for node in self._nodes])

    def to_text(self, style = {}, **kwargs):
        if (len(self._nodes) == 0):
            return ''

        full_style = copy.deepcopy(style)
        full_style.update(self._style)

        return "\n".join([node.to_text(style = full_style, **kwargs) for node in self._nodes])

    def to_tex(self, style = {}, **kwargs):
        if (len(self._nodes) == 0):
            return ''

        full_style = copy.deepcopy(style)
        full_style.update(self._style)

        prefixes, suffixes = self._compute_tex_fixes(full_style)
        node_content = [node.to_tex(style = full_style, **kwargs) for node in self._nodes]

        content = prefixes + node_content + list(reversed(suffixes))

        return "\n".join(content)

    def _compute_tex_fixes(self, style):
        # The beginning and ends of groups.
        # These will match 1-1.
        prefixes = []
        suffixes = []

        content_align = quizgen.parser.style.get_alignment(style, quizgen.parser.style.KEY_CONTENT_ALIGN)
        if (content_align is not None):
            env_name = TEX_BLOCK_ALIGNMENT[content_align]
            prefixes.append("\\begin{%s}" % (env_name))
            suffixes.append("\\end{%s}" % (env_name))

        font_size = style.get(quizgen.parser.style.KEY_FONT_SIZE, None)
        if (font_size is not None):
            font_size = float(font_size)
            # 1.2 is the default size for baseline skip relative to font size.
            # See: https://ctan.math.illinois.edu/macros/latex/contrib/fontsize/fontsize.pdf
            baseline_skip = 1.2 * font_size

            prefixes.append('\\begingroup\\fontsize{%.2fpt}{%.2fpt}\\selectfont' % (font_size, baseline_skip))
            suffixes.append('\\endgroup')

        return prefixes, suffixes

    def to_html(self, style = {}, **kwargs):
        if (len(self._nodes) == 0):
            return ''

        full_style = copy.deepcopy(style)
        full_style.update(self._style)

        content = "\n".join([node.to_html(style = full_style, **kwargs) for node in self._nodes])
        style_string = self._compute_html_style_string(full_style)

        return "<div class='block' %s>\n%s\n</div>" % (style_string, content)

    def _compute_html_style_string(self, style):
        attributes = [
            'margin-bottom: 1em',
        ]

        content_align = quizgen.parser.style.get_alignment(style, quizgen.parser.style.KEY_CONTENT_ALIGN)
        if (content_align is not None):
            attributes.append("display: flex")
            attributes.append("flex-direction: column")
            attributes.append("justify-content: flex-start")
            attributes.append("align-items: %s" % (FLEXBOX_ALIGNMENT[content_align]))

        text_align = quizgen.parser.style.get_alignment(style, quizgen.parser.style.KEY_TEXT_ALIGN)
        if (text_align is not None):
            attributes.append("text-align: %s" % (text_align))

        font_size = style.get(quizgen.parser.style.KEY_FONT_SIZE, None)
        if (font_size is not None):
            attributes.append("font-size: %.2fpt" % (float(font_size)))

        if (len(attributes) == 0):
            return ''

        return "style='%s'" % ('; '.join(attributes))

    def to_pod(self, **kwargs):
        data = {
            "type": "block",
            "nodes": [node.to_pod(**kwargs) for node in self._nodes],
        }

        if (len(self._style) > 0):
            data['style'] = self._style

        return data

    def collect_file_paths(self, base_dir):
        paths = []

        for node in self._nodes:
            paths += node.collect_file_paths(base_dir)

        return paths

    def is_empty(self):
        return (len(self._nodes) == 0)

    # A block node can be "lifted" (absorbed by the parent) if it has no style.
    def is_liftable(self):
        return (len(self._style) == 0)

class StyleNode(ParseNode):
    def __init__(self, style = {}):
        self._style = style

    def to_markdown(self, **kwargs):
        raise RuntimeError("Style nodes should not be in the AST.")

    def to_text(self, **kwargs):
        raise RuntimeError("Style nodes should not be in the AST.")

    def to_tex(self, **kwargs):
        raise RuntimeError("Style nodes should not be in the AST.")

    def to_html(self, **kwargs):
        raise RuntimeError("Style nodes should not be in the AST.")

    def to_pod(self, **kwargs):
        return self._style
