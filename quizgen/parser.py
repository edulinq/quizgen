import abc
import base64
import copy
import html
import json
import os
import re

import json5
import lark
import lark.visitors

import quizgen.katex
import quizgen.util.file

ENCODING = 'utf-8'

GRAMMAR = r'''
    document: blocks
    blocks: [ block ( NEWLINE+ block )* NEWLINE* ]

    block: ( ( explicit_block | style_block | code_block | equation_block | table_block | list_block | text_line ) NEWLINE )+

    explicit_block: "{-" NEWLINE+ blocks "-}"

    style_block: "{{" NEWLINE? style_block_internal "}}"
    ?style_block_internal: /.+?(?=\}\})/s

    code_block: "```" NEWLINE? code_block_internal "```"
    ?code_block_internal: /.+?(?=```)/s

    equation_block: "$$" NEWLINE? equation_block_internal "$$"
    ?equation_block_internal: /.+?(?=\$\$)/s

    table_block: ( ( table_head | table_row | table_sep ) NEWLINE )+
    table_sep: /\|-{3}[-\s]*\|.*/
    table_row: "|" table_cell+
    table_head: "|-" table_cell+
    table_cell: text_line "|"

    list_block: ( LIST_ITEM_START text_line NEWLINE )+
    LIST_ITEM_START: /\s*-/

    text_line: ( text_line_internal )+
    ?text_line_internal: inline_comment
                       | inline_code
                       | inline_equation
                       | inline_italics
                       | inline_bold
                       | inline_link
                       | inline_image
                       | inline_linebreak
                       | inline_answer_reference
                       | inline_text

    inline_comment: /\s*\/\// INLINE_COMMENT
    inline_link: INLINE_LINK_TEXT INLINE_LINK_LINK
    inline_image: "!" INLINE_LINK_TEXT INLINE_LINK_LINK
    inline_code: INLINE_CODE
    inline_equation: INLINE_EQUATION
    inline_italics: INLINE_ITALICS
    inline_bold: INLINE_BOLD
    inline_linebreak: "\\n"
    inline_answer_reference: "[[" REFERENCE_WORD "]]"
    inline_text: ( ESC_CHAR | NON_ESC_TEXT )+

    _ESCAPE_INTERNAL: /.+?/ /(?<!\\)(\\\\)*?/

    INLINE_COMMENT: /.*?\n/s
    INLINE_CODE: "`" _ESCAPE_INTERNAL "`"
    INLINE_EQUATION: "$" _ESCAPE_INTERNAL "$"
    INLINE_ITALICS: "*" _ESCAPE_INTERNAL "*"
    INLINE_BOLD: "**" _ESCAPE_INTERNAL "**"
    INLINE_LINK_TEXT: "[" _ESCAPE_INTERNAL "]"
    INLINE_LINK_LINK: "(" _ESCAPE_INTERNAL ")"

    REFERENCE_WORD: /[a-zA-Z][a-zA-Z0-9_]*/

    NON_ESC_TEXT: NON_ESC_CHAR+
    NON_ESC_CHAR: /[^\n\\`|\*\$\-\[{!\/]/x
    ESC_CHAR: "\\\\"
            | "\\-"
            | "\\*"
            | "\\|"
            | "\\$"
            | "\\["
            | "\\{"
            | "\\!"
            | "\\`"
            | "\\/"

    NEWLINE: /\n/
'''

TEX_REPLACEMENTS = {
    # Specially handle braces and slashes to avoid clobbering other replacements.
    '{': 'ZZZzzz  OPEN BRACE REPLACEMENT  zzzZZZ',
    '}': 'ZZZzzz  CLOSE BRACE REPLACEMENT  zzzZZZ',
    '\\': 'ZZZzzz  BACKSLASH REPLACEMENT  zzzZZZ',

    '|': '\\textbar{}',
    '$': '\\$',
    '#': '\\#',
    '%': '\\%',
    '_': '\\_',
    'π': '$\\pi$',
    '`': '\\`{}',

    'ZZZzzz  OPEN BRACE REPLACEMENT  zzzZZZ': '\\{',
    'ZZZzzz  CLOSE BRACE REPLACEMENT  zzzZZZ': '\\}',
    'ZZZzzz  BACKSLASH REPLACEMENT  zzzZZZ': '\\textbackslash{}',
}

VERB_CHARACTERS = ['|', '!', '@', '#', '$', '^', '&', '-', '_', '=', '+']

STYLE_KEY_CONTENT_ALIGN = 'content-align'
STYLE_KEY_FONT_SIZE = 'font-size'
STYLE_KEY_IMAGE_WIDTH = 'image-width'
STYLE_KEY_TABLE_BORDER_CELLS = 'table-border-cells'
STYLE_KEY_TABLE_BORDER_TABLE = 'table-border-table'
STYLE_KEY_TABLE_CELL_HEIGHT = 'table-cell-height'
STYLE_KEY_TABLE_CELL_WIDTH = 'table-cell-width'
STYLE_KEY_TABLE_HEAD_BOLD = 'table-head-bold'
STYLE_KEY_TEXT_ALIGN = 'text-align'

STYLE_DEFAULT_IMAGE_WIDTH = 1.0
STYLE_DEFAULT_TABLE_BORDER_CELLS = False
STYLE_DEFAULT_TABLE_BORDER_TABLE = False
STYLE_DEFAULT_TABLE_CELL_HEIGHT = 1.5
STYLE_DEFAULT_TABLE_CELL_WIDTH = 1.5
STYLE_DEFAULT_TABLE_HEAD_BOLD = True

STYLE_ALLOWED_VALUES_ALIGNMENT_LEFT = 'left'
STYLE_ALLOWED_VALUES_ALIGNMENT_CENTER = 'center'
STYLE_ALLOWED_VALUES_ALIGNMENT_RIGHT = 'right'
STYLE_ALLOWED_VALUES_ALIGNMENT = [
    STYLE_ALLOWED_VALUES_ALIGNMENT_LEFT,
    STYLE_ALLOWED_VALUES_ALIGNMENT_CENTER,
    STYLE_ALLOWED_VALUES_ALIGNMENT_RIGHT
]

FLEXBOX_ALIGNMENT = {
    STYLE_ALLOWED_VALUES_ALIGNMENT_LEFT: 'flex-start',
    STYLE_ALLOWED_VALUES_ALIGNMENT_CENTER: 'center',
    STYLE_ALLOWED_VALUES_ALIGNMENT_RIGHT: 'flex-end',
}

TEX_BLOCK_ALIGNMENT = {
    STYLE_ALLOWED_VALUES_ALIGNMENT_LEFT: 'flushleft',
    STYLE_ALLOWED_VALUES_ALIGNMENT_CENTER: 'center',
    STYLE_ALLOWED_VALUES_ALIGNMENT_RIGHT: 'flushright',
}

TEX_TEXT_TABLE_ALIGNMENT = {
    STYLE_ALLOWED_VALUES_ALIGNMENT_LEFT: 'l',
    STYLE_ALLOWED_VALUES_ALIGNMENT_CENTER: 'c',
    STYLE_ALLOWED_VALUES_ALIGNMENT_RIGHT: 'r',
}

HTML_BORDER_SPEC = '1px solid black'

class DocTransformer(lark.Transformer):
    def document(self, blocks):
        return DocumentNode(blocks[0])

    def blocks(self, blocks):
        return blocks

    def block(self, nodes):
        # Lift blocks and style up.
        if ((len(nodes) == 1) and isinstance(nodes[0], (BlockNode, StyleNode))):
            return nodes[0]

        return BlockNode(nodes)

    def explicit_block(self, nodes):
        return BlockNode(nodes[0])

    def style_block(self, text):
        text = '{' + text[0].strip("\n") + '}'
        try:
            data = json5.loads(text)
        except Exception as ex:
            raise ValueError("Style is not valid JSON.") from ex

        return StyleNode(data)

    def code_block(self, text):
        # Trim any newlines.
        text = text[0].strip("\n")
        return CodeNode(text, inline = False)

    def equation_block(self, text):
        # Trim any newlines.
        text = text[0].strip()
        return EquationNode(text, inline = False)

    def text_line(self, nodes):
        return TextNode(nodes)

    def inline_comment(self, text):
        return CommentNode(str(text[1]).strip())

    def inline_text(self, text):
        return NormalTextNode(''.join(text))

    def inline_linebreak(self, _):
        return LinebreakNode()

    def inline_answer_reference(self, text):
        return AnswerReferenceNode(str(text[0]))

    def inline_italics(self, text):
        # Strip off the asterisks.
        text = str(text[0])[1:-1]
        return ItalicsNode(text)

    def inline_bold(self, text):
        # Strip off the asterisks.
        text = str(text[0])[2:-2]
        return BoldNode(text)

    def inline_code(self, text):
        # Strip off the backticks.
        text = str(text[0])[1:-1]

        # Replace any escaped backticks.
        text = text.replace(r'\`', '`')

        return CodeNode(text, inline = True)

    def inline_equation(self, text):
        # Strip off the dollar signs.
        text = str(text[0])[1:-1].strip()

        # Replace any escaped dollar signs.
        text = text.replace(r'\$', '$')

        return EquationNode(text, inline = True)

    def table_block(self, rows):
        return TableNode(rows)

    def table_row(self, cells):
        return TableRowNode(cells, head = False)

    def table_head(self, cells):
        return TableRowNode(cells, head = True)

    def table_sep(self, cells):
        return TableSepNode()

    def table_cell(self, cell):
        return cell[0].trim()

    def list_block(self, items):
        return ListNode([item.trim() for item in items])

    def inline_link(self, contents):
        # Remove the surrounding characters, strip it, and replace escaped end markers.
        text = str(contents[0])[1:-1].strip().replace(r'\]', ']')
        link = str(contents[1])[1:-1].strip().replace(r'\)', ')')

        return LinkNode(text, link)

    def inline_image(self, contents):
        text = str(contents[0])[1:-1].strip()
        link = str(contents[1])[1:-1].strip()

        return ImageNode(text, link)

    def NON_ESC_TEXT(self, text):
        return str(text)

    def ESC_CHAR(self, text):
        # Remove the backslash.
        return text[1:]

    def LIST_ITEM_START(self, token):
        return lark.visitors.Discard

    def NEWLINE(self, token):
        return lark.visitors.Discard

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

    def to_json(self, indent = 4, **kwargs):
        return json.dumps(self.to_pod(**kwargs), indent = indent)

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
            "type": "document",
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

        content_align = _get_alignment(style, STYLE_KEY_CONTENT_ALIGN)
        if (content_align is not None):
            env_name = TEX_BLOCK_ALIGNMENT[content_align]
            prefixes.append("\\begin{%s}" % (env_name))
            suffixes.append("\\end{%s}" % (env_name))

        font_size = style.get(STYLE_KEY_FONT_SIZE, None)
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

        content_align = _get_alignment(style, STYLE_KEY_CONTENT_ALIGN)
        if (content_align is not None):
            attributes.append("display: flex")
            attributes.append("flex-direction: column")
            attributes.append("justify-content: flex-start")
            attributes.append("align-items: %s" % (FLEXBOX_ALIGNMENT[content_align]))

        text_align = _get_alignment(style, STYLE_KEY_TEXT_ALIGN)
        if (text_align is not None):
            attributes.append("text-align: %s" % (text_align))

        font_size = style.get(STYLE_KEY_FONT_SIZE, None)
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

class LinkNode(ParseNode):
    def __init__(self, text, link):
        self._text = text
        self._link = link

    def to_markdown(self, **kwargs):
        return f"[{self._text}]({self._link})"

    def to_text(self, **kwargs):
        return f"{self._text} ({self._link})"

    def to_tex(self, **kwargs):
        if (self._text == ""):
            return rf"\url{{{self._link}}}"

        return rf"\href{{{self._link}}}{{{self._text}}}"

    def to_html(self, **kwargs):
        text = self._text
        if (text == ''):
            text = self._link

        return f"<a href='{self._link}'>{text}</a>"

    def to_pod(self, **kwargs):
        return {
            "type": "link",
            "text": self._text,
            "link": self._link,
        }

class ImageNode(ParseNode):
    def __init__(self, text, link):
        self._text = text
        self._link = link

        self._computed_path = None

    def to_markdown(self, **kwargs):
        return self.to_html(**kwargs)

    def to_text(self, base_dir = '.', image_path_callback = None, **kwargs):
        self._handle_callback(image_path_callback, base_dir)
        return f"{self._text} ({self._computed_path})"

    def to_tex(self, base_dir = '.', style = {}, image_path_callback = None, **kwargs):
        self._handle_callback(image_path_callback, base_dir)

        width = self._get_width(style)
        return r"\includegraphics[width=%0.2f\textwidth]{%s}" % (width, self._computed_path)

    def to_html(self, base_dir = '.', canvas_instance = None,
            force_raw_image_src = False, image_path_callback = None,
            style = {},
            **kwargs):
        self._handle_callback(image_path_callback, base_dir)
        path = os.path.realpath(os.path.join(base_dir, self._computed_path))

        attr = {
            'alt': self._text,
            'width': "%5.2f%%" % (100.0 * self._get_width(style)),
        }

        if (force_raw_image_src or re.match(r'^http(s)?://', self._computed_path)):
            attr['src'] = self._computed_path
        elif (canvas_instance is not None):
            # Canvas requires uploading the image, which should have been done via Canvas uploader.
            file_id = canvas_instance.context.get('file_ids', {}).get(path)
            if (file_id is None):
                raise ValueError(f"Could not get canvas context file id of image '{path}'.")

            attr['src'] = f"{canvas_instance.base_url}/courses/{canvas_instance.course_id}/files/{file_id}/preview"
        else:
            # If we are not uploading to canvas or using a raw source, do a base64 encode of the image.
            mime, content = encode_image(path)
            attr['src'] = f"data:{mime};base64,{content}"

        content = []
        for (key, value) in sorted(attr.items()):
            value = str(value).replace("'", r"\'")
            content.append("%s='%s'" % (key, value))

        return "<img %s />" % (' '.join(content))

    def _get_width(self, style):
        width = style.get(STYLE_KEY_IMAGE_WIDTH, None)
        if (width is None):
            width = STYLE_DEFAULT_IMAGE_WIDTH

        return float(width)

    def collect_file_paths(self, base_dir):
        if (re.match(r'^http(s)?://', self._link)):
            return []

        path = os.path.realpath(os.path.join(base_dir, self._link))
        return [path]

    def to_pod(self, **kwargs):
        return {
            "type": "image",
            "text": self._text,
            "link": self._link,
        }

    def _handle_callback(self, image_path_callback, base_dir):
        if (self._computed_path is not None):
            return

        if (image_path_callback is None):
            self._computed_path = self._link
        else:
            self._computed_path = image_path_callback(self._link, base_dir)

class TableNode(ParseNode):
    def __init__(self, rows):
        self._rows = list(rows)

        self._width = 0
        for row in self._rows:
            self._width = max(self._width, len(row))

    def to_markdown(self, **kwargs):
        return "\n".join([row.to_markdown(width = self._width, **kwargs) for row in self._rows]) + "\n"

    def to_text(self, **kwargs):
        return "\n".join([row.to_text(width = self._width, **kwargs) for row in self._rows]) + "\n"

    def to_tex(self, style = {}, **kwargs):
        border_table = _get_boolean_style_key(style, STYLE_KEY_TABLE_BORDER_TABLE, STYLE_DEFAULT_TABLE_BORDER_TABLE)
        border_cells = _get_boolean_style_key(style, STYLE_KEY_TABLE_BORDER_CELLS, STYLE_DEFAULT_TABLE_BORDER_CELLS)
        alignment = _get_alignment(style, STYLE_KEY_TEXT_ALIGN, default_value = STYLE_ALLOWED_VALUES_ALIGNMENT_CENTER)

        column_align = TEX_TEXT_TABLE_ALIGNMENT[alignment]

        column_join = ''
        if (border_cells):
            column_join = '|'

        column_spec = column_join.join([column_align] * self._width)

        if (border_table):
            column_spec = '|' + column_spec + '|'

        lines = [
            r'\begin{tabular}{ ' + column_spec + ' }',
        ]

        if (border_table):
            lines.append(r'\hline')

        for i in range(len(self._rows)):
            row = self._rows[i]

            if (border_cells and isinstance(row, TableSepNode)):
                continue

            if (border_cells and (i > 0)):
                lines.append(r'\hline')

            row = row.to_tex(width = self._width, style = style, **kwargs)
            lines.append(f"{row}")

        if (border_table):
            lines.append(r'\hline')

        lines += [
            r'\end{tabular}',
        ]

        lines = self._apply_tex_table_style(style, lines)

        return "\n".join(lines)

    def to_html(self, style = {}, **kwargs):
        table_style = [
            'border-collapse: collapse',
        ]

        if (_get_boolean_style_key(style, STYLE_KEY_TABLE_BORDER_TABLE, STYLE_DEFAULT_TABLE_BORDER_TABLE)):
            table_style.append("border: %s" % HTML_BORDER_SPEC)
        else:
            table_style.append('border-style: hidden')

        # HTML tables require extra encouragement to align.
        text_align = _get_alignment(style, STYLE_KEY_TEXT_ALIGN)
        if (text_align is not None):
            table_style.append("text-align: %s" % (text_align))

        table_style_string = '; '.join(table_style)
        lines = [
            "<table style='%s'>" % (table_style_string)
        ]

        next_cell_style = {}
        for row in self._rows:
            if (isinstance(row, TableSepNode)):
                next_cell_style = {'border-top': "%s" % (HTML_BORDER_SPEC)}
            else:
                lines.append(row.to_html(extra_cell_style = next_cell_style, style = style, **kwargs))
                next_cell_style = {}

        lines += [
            '</table>'
            '',
        ]

        return "\n".join(lines)

    def to_pod(self, **kwargs):
        return {
            "type": "table",
            "rows": [row.to_pod(**kwargs) for row in self._rows],
        }

    def collect_file_paths(self, base_dir):
        paths = []

        for row in self._rows:
            paths += row.collect_file_paths(base_dir)

        return paths

    def _apply_tex_table_style(self, style, lines):
        # Height
        height = max(1.0, float(style.get(STYLE_KEY_TABLE_CELL_HEIGHT, STYLE_DEFAULT_TABLE_CELL_HEIGHT)))
        prefix = [
            r'\begingroup',
            r'\renewcommand{\arraystretch}{%0.2f}' % (height),
        ]
        lines = prefix + lines
        lines.append(r'\endgroup')

        # Width
        width = max(1.0, float(style.get(STYLE_KEY_TABLE_CELL_WIDTH, STYLE_DEFAULT_TABLE_CELL_WIDTH)))
        prefix = [
            r'\begingroup',
            r'\setlength{\tabcolsep}{%0.2fem}' % (width),
        ]
        lines = prefix + lines
        lines.append(r'\endgroup')

        return lines

class TableRowNode(ParseNode):
    def __init__(self, cells, head = False):
        self._cells = list(cells)
        self._head = head

    def to_markdown(self, **kwargs):
        return "| " + " | ".join([cell.to_markdown(**kwargs) for cell in self._cells]) + " |"

    def to_text(self, **kwargs):
        return "| " + " | ".join([cell.to_text(**kwargs) for cell in self._cells]) + " |"

    def to_tex(self, style = {}, **kwargs):
        cells_text = [cell.to_tex(style = style, **kwargs) for cell in self._cells]

        if (self._head and _get_boolean_style_key(style, STYLE_KEY_TABLE_HEAD_BOLD, STYLE_DEFAULT_TABLE_HEAD_BOLD)):
            cells_text = [BoldNode.bold_tex(text) for text in cells_text]

        return " & ".join(cells_text) + r' \\'

    def to_html(self, extra_cell_style = {}, style = {}, **kwargs):
        tag = 'td'
        if (self._head):
            tag = 'th'

            weight = 'normal'
            if (_get_boolean_style_key(style, STYLE_KEY_TABLE_HEAD_BOLD, STYLE_DEFAULT_TABLE_HEAD_BOLD)):
                weight = 'bold'

            extra_cell_style['font-weight'] = "%s" % (weight)

        lines = ['<tr>']

        cell_style = self._compute_cell_style(style, extra_cell_style = extra_cell_style)
        cell_style_string = '; '.join([': '.join(item) for item in cell_style.items()])

        for cell in self._cells:
            content = cell.to_html(style = style, **kwargs)
            content = f"<%s style='%s'>%s</%s>" % (tag, cell_style_string, content, tag)
            lines.append(content)

        lines += ['</tr>']

        return "\n".join(lines)

    def to_pod(self, **kwargs):
        return {
            "type": "table-row",
            "head": self._head,
            "cells": [cell.to_pod(**kwargs) for cell in self._cells],
        }

    def collect_file_paths(self, base_dir):
        paths = []

        for cell in self._cells:
            paths += cell.collect_file_paths(base_dir)

        return paths

    def __len__(self):
        return len(self._cells)

    def _compute_cell_style(self, style, extra_cell_style = {}):
        height = max(1.0, float(style.get(STYLE_KEY_TABLE_CELL_HEIGHT, STYLE_DEFAULT_TABLE_CELL_HEIGHT)))
        vertical_padding = height - 1.0

        width = max(1.0, float(style.get(STYLE_KEY_TABLE_CELL_WIDTH, STYLE_DEFAULT_TABLE_CELL_WIDTH)))
        horizontal_padding = width - 1.0

        cell_style = {
            'padding-top': "%0.2fem" % (vertical_padding / 2),
            'padding-bottom': "%0.2fem" % (vertical_padding / 2),

            'padding-left': "%0.2fem" % (horizontal_padding / 2),
            'padding-right': "%0.2fem" % (horizontal_padding / 2),
        }

        if (_get_boolean_style_key(style, STYLE_KEY_TABLE_BORDER_CELLS, STYLE_DEFAULT_TABLE_BORDER_CELLS)):
            cell_style['border'] = "%s" % (HTML_BORDER_SPEC)

        cell_style.update(extra_cell_style)

        return cell_style

class TableSepNode(ParseNode):
    def __init__(self):
        pass

    def to_markdown(self, width = 1, **kwargs):
        return "|" + ("---|" * width)

    def to_text(self, width = 1, **kwargs):
        return "|" + ("---|" * width)

    def to_tex(self, **kwargs):
        return r'\hline'

    def to_html(self, **kwargs):
        raise RuntimeError("to_html() should never be called on a table separator (row should handle it).")

    def to_pod(self, **kwargs):
        return {
            "type": "table-sep",
        }

    def __len__(self):
        return 1

class ListNode(ParseNode):
    def __init__(self, items):
        self._items = list(items)

    def to_markdown(self, **kwargs):
        return "\n".join([" - " + item.to_markdown(**kwargs) for item in self._items]) + "\n"

    def to_text(self, **kwargs):
        return "\n".join([" - " + item.to_text(**kwargs) for item in self._items]) + "\n"

    def to_tex(self, **kwargs):
        lines = [
            r'\begin{itemize}',
        ]

        for item in self._items:
            text = item.to_tex(**kwargs)
            lines.append(f"    \item {text}")

        lines += [
            r'\end{itemize}',
            '',
        ]

        return "\n".join(lines)

    def to_html(self, **kwargs):
        lines = [
            '<ul style="margin-bottom: 0; margin-top: 0;">',
        ]

        for item in self._items:
            text = item.to_html(**kwargs)
            lines.append(f'<li>{text}</li>')

        lines += [
            '</ul>'
            '',
        ]

        return "\n".join(lines)

    def to_pod(self, **kwargs):
        return {
            "type": "list",
            "items": [item.to_pod(**kwargs) for item in self._items],
        }

    def collect_file_paths(self, base_dir):
        paths = []

        for item in self._items:
            paths += item.collect_file_paths(base_dir)

        return paths

class TextNode(ParseNode):
    def __init__(self, nodes):
        self._nodes = list(nodes)

    def to_markdown(self, **kwargs):
        return "".join([node.to_markdown(**kwargs) for node in self._nodes])

    def to_text(self, **kwargs):
        return "".join([node.to_text(**kwargs) for node in self._nodes])

    def to_tex(self, **kwargs):
        return "".join([node.to_tex(**kwargs) for node in self._nodes])

    def to_html(self, **kwargs):
        return "".join([node.to_html(**kwargs) for node in self._nodes])

    def to_pod(self, **kwargs):
        return {
            "type": "text",
            "nodes": [node.to_pod(**kwargs) for node in self._nodes],
        }

    def trim(self, left = True, right = True):
        """
        Trim the whitespace off the edges of this node.
        """

        if (left):
            self._nodes[0].trim(right = False)

        if (right):
            self._nodes[-1].trim(left = False)

        if (self._nodes[0].is_empty()):
            self._nodes.pop(0)

        if ((len(self._nodes) > 0) and (self._nodes[-1].is_empty())):
            self._nodes.pop()

        return self

    def collect_file_paths(self, base_dir):
        paths = []

        for node in self._nodes:
            paths += node.collect_file_paths(base_dir)

        return paths

class LinebreakNode(ParseNode):
    def __init__(self):
        pass

    def to_markdown(self, **kwargs):
        return "  \n"

    def to_text(self, **kwargs):
        return "\n\n"

    def to_tex(self, **kwargs):
        return ' \\newline\n'

    def to_html(self, **kwargs):
        return "<br />"

    def to_pod(self, **kwargs):
        return {
            "type": "linebreak",
        }

class BaseTextNode(ParseNode):
    def __init__(self, text, type):
        self._text = text
        self._type = type

    def to_pod(self, **kwargs):
        return {
            "type": self._type,
            "text": self._text,
        }

    def trim(self, left = True, right = True):
        if (left):
            self._text = self._text.lstrip()

        if (right):
            self._text = self._text.rstrip()

        return self

    def is_empty(self):
        return (len(self._text) == 0)

class AnswerReferenceNode(BaseTextNode):
    def __init__(self, text):
        super().__init__(text, 'answer-reference')

    def to_markdown(self, **kwargs):
        return f"[[{self._text}]]"

    def to_text(self, **kwargs):
        return f"[{self._text}]"

    def to_tex(self, **kwargs):
        # TODO(eriq): We do not have a convention for this.
        text = tex_escape(self._text)
        return rf"\textsc{{<{text}>}}"

    def to_html(self, **kwargs):
        text = html.escape(self._text)
        return f"<span>[{text}]</span>"

class CommentNode(BaseTextNode):
    def __init__(self, text):
        super().__init__(text, 'comment')

    def to_markdown(self, display_comments = False, **kwargs):
        if (not display_comments):
            return ""

        return f"<!--- {self._text} -->"

    def to_text(self, display_comments = False, **kwargs):
        if (not display_comments):
            return ""

        return f"# {self._text}"

    def to_tex(self, display_comments = False, **kwargs):
        if (not display_comments):
            return ""

        return f"% {self._text}"

    def to_html(self, display_comments = False, **kwargs):
        if (not display_comments):
            return ""

        text = html.escape(self._text)
        return f"<!--- {text} -->"

class NormalTextNode(BaseTextNode):
    def __init__(self, text):
        super().__init__(text, 'normal_text')

    def to_markdown(self, **kwargs):
        return self._text

    def to_text(self, **kwargs):
        return self._text

    def to_tex(self, **kwargs):
        return tex_escape(self._text)

    def to_html(self, **kwargs):
        text = html.escape(self._text)
        return f"<span>{text}</span>"

class ItalicsNode(BaseTextNode):
    def __init__(self, text):
        super().__init__(text, 'italics_text')

    def to_markdown(self, **kwargs):
        return f"*{self._text}*"

    def to_text(self, **kwargs):
        return self._text

    def to_tex(self, **kwargs):
        text = tex_escape(self._text)
        return rf"\textit{{{text}}}"

    def to_html(self, **kwargs):
        text = html.escape(self._text)
        return f"<span><emph>{text}</emph></span>"

class BoldNode(BaseTextNode):
    def __init__(self, text):
        super().__init__(text, 'bold_text')

    def to_markdown(self, **kwargs):
        return f"**{self._text}**"

    def to_text(self, **kwargs):
        return self._text

    def to_tex(self, **kwargs):
        return BoldNode.bold_tex(self._text)

    def to_html(self, **kwargs):
        text = html.escape(self._text)
        return f"<span><strong>{text}</strong></span>"

    @classmethod
    def bold_tex(cls, text, escape = True):
        text = tex_escape(text)
        return rf"\textbf{{{text}}}"

class CodeNode(BaseTextNode):
    def __init__(self, text, inline = False):
        super().__init__(text, 'code')
        self._inline = inline

    def to_markdown(self, **kwargs):
        if (self._inline):
            return f"`{self._text}`"

        return f"```\n{self._text}\n```"

    def to_text(self, bare = False, **kwargs):
        if (bare and self._inline):
            return f"{self._text}"
        elif (bare and (not self._inline)):
            return f"\n{self._text}\n"
        elif ((not bare) and self._inline):
            return f"`{self._text}`"
        else:
            return f"```\n{self._text}\n```"

    def to_tex(self, **kwargs):
        if (not self._inline):
            return f"\\begin{{lstlisting}}\n{self._text}\n\\end{{lstlisting}}"

        delim = None
        for char in VERB_CHARACTERS:
            if (char not in self._text):
                delim = char
                break

        if (delim is None):
            raise ValueError("Could not find a delimiter to use with tex's `\verb'.")

        return r"\verb%s%s%s" % (delim, self._text, delim)

    def to_html(self, **kwargs):
        content = f'<code>{self._text}</code>'

        if (not self._inline):
            content = f"<pre style='margin: 1em'>{content}</pre>"

        return content

    def to_pod(self, **kwargs):
        value = super().to_pod(**kwargs)
        value["inline"] = self._inline

        return value

class EquationNode(BaseTextNode):
    katex_available = None

    def __init__(self, text, inline = False):
        super().__init__(text, 'equation')
        self._inline = inline

    def to_markdown(self, **kwargs):
        if (self._inline):
            return f"$ {self._text} $"

        return f"$$\n{self._text}\n$$"

    def to_text(self, bare = False, **kwargs):
        if (not bare):
            return self.to_tex()

        if (self._inline):
            return f"{self._text}"

        return f"\n{self._text}\n"

    def to_tex(self, **kwargs):
        text = self._text.replace('$', '\$')

        if (self._inline):
            return f"$ {text} $"

        return f"$$\n{text}\n$$"

    def to_html(self, **kwargs):
        if (EquationNode.katex_available is None):
            EquationNode.katex_available = quizgen.katex.is_available()

        content = f"<code>{self._text}</code>"
        if (EquationNode.katex_available):
            content = quizgen.katex.to_html(self._text)

        element = 'p'
        if (self._inline):
            element = 'span'

        return f"<{element}>{content}</{element}>"

    def to_pod(self, **kwargs):
        value = super().to_pod(**kwargs)
        value["inline"] = self._inline

        return value

def encode_image(path):
    ext = os.path.splitext(path)[-1].lower()
    mime = f"image/{ext}"

    with open(path, 'rb') as file:
        data = file.read()

    content = base64.standard_b64encode(data)
    return mime, content.decode(ENCODING)

def tex_escape(text):
    """
    Prepare normal text for tex.
    """

    for key, value in TEX_REPLACEMENTS.items():
        text = text.replace(key, value)

    return text

def _get_alignment(style, key, default_value = None):
    alignment = style.get(key, None)
    if (alignment is None):
        return default_value

    alignment = str(alignment).lower()
    if (alignment not in STYLE_ALLOWED_VALUES_ALIGNMENT):
        raise ValueError("Unknown value for '%s' style key '%s'. Allowed values: '%s'." % (key, alignment, STYLE_ALLOWED_VALUES_ALIGNMENT))

    return alignment

def _get_boolean_style_key(style, key, default_value = None):
    value = style.get(key, default_value)
    if (value is None):
        return default_value

    return (value is True)

def clean_text(text):
    # Remove carriage returns.
    text = text.replace("\r", '')

    # Trim whitespace.
    text = text.strip();

    # Replace the final newline and add one additional one (for tables).
    text += "\n\n"

    return text

def parse_text(text, base_dir = '.'):
    # Special case for empty documents.
    if (text.strip() == ''):
        return DocumentNode([])

    text = clean_text(text)

    parser = lark.Lark(GRAMMAR, start = 'document')
    ast = parser.parse(text)

    document = DocTransformer().transform(ast)
    document.set_base_dir(base_dir)

    return document

def parse_file(path):
    if (not os.path.isfile(path)):
        raise ValueError(f"Path to parse ('{path}') is not a file.")

    text = quizgen.util.file.read(path)
    base_dir = os.path.dirname(path)

    return parse_text(text, base_dir = base_dir)
