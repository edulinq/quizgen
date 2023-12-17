import abc
import base64
import copy
import html
import json
import os
import re

import lark
import lark.visitors

import quizgen.katex
import quizgen.util.file

ENCODING = 'utf-8'

GRAMMAR = r'''
    document: [ block ( NEWLINE+ block )* NEWLINE* ]

    block: ( ( code_block | equation_block | table_block | list_block | text_line ) NEWLINE )+

    code_block: "```" NEWLINE? code_block_internal "```"
    ?code_block_internal: /.+?(?=```)/s
    CODE_BLOCK_TERMINAL: "```"

    equation_block: "$$" NEWLINE? equation_block_internal "$$"
    ?equation_block_internal: /.+?(?=\$\$)/s

    table_block: ( ( table_head | table_row | table_sep ) NEWLINE )+
    table_sep: /\|-{3,}\|.*/
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

    REFERENCE_WORD: /[a-zA-Z][a-zA-Z0-9]*/

    NON_ESC_TEXT: NON_ESC_CHAR+
    NON_ESC_CHAR: /[^\n\\`|\*\$\-\[!\/]/x
    ESC_CHAR: "\\\\"
            | "\\-"
            | "\\*"
            | "\\|"
            | "\\$"
            | "\\["
            | "\\!"
            | "\\`"
            | "\\/"

    NEWLINE: /\n/
'''

TEX_REPLACEMENTS = {
    '\\': '\\textbackslash{}',
    '|': '\\textbar{}',
    '`': '\\`{}',
}

TEX_HEADER = r'''\documentclass[12pt]{article}

\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsthm}
\usepackage{booktabs}
\usepackage{courier}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{times}
\usepackage{listings}

\begin{document}
'''

TEX_FOOTER = r'''
\end{document}'''

HTML_TABLE_STYLE = [
    'border-collapse: collapse',
    'text-align: center',
    'margin-bottom: 1em',
]

VERB_CHARACTERS = ['|', '!', '@', '#', '$', '^', '&', '-', '_', '=', '+']

class DocTransformer(lark.Transformer):
    def document(self, blocks):
        return DocumentNode(blocks)

    def block(self, nodes):
        return BlockNode(nodes)

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
        if (format == quizgen.constants.DOC_FORMAT_HTML):
            return self.to_html(**kwargs)
        elif (format == quizgen.constants.DOC_FORMAT_JSON):
            return self.to_json(**kwargs)
        elif (format == quizgen.constants.DOC_FORMAT_MD):
            return self.to_markdown(**kwargs)
        elif (format == quizgen.constants.DOC_FORMAT_TEX):
            return self.to_tex(**kwargs)
        elif (format == quizgen.constants.DOC_FORMAT_TEXT):
            return self.to_tex(**kwargs)
        else:
            raise ValueError(f"Unknown format '{format}'.")

class DocumentNode(ParseNode):
    def __init__(self, nodes):
        self._nodes = list(nodes)
        self._context = {}

    def set_context(self, key, value):
        self._context[key] = value

    def set_base_dir(self, base_dir):
        self.set_context("base_dir", base_dir)

    def to_markdown(self, **kwargs):
        context = copy.deepcopy(self._context)
        context.update(kwargs)

        return "\n\n".join([node.to_markdown(**context) for node in self._nodes])

    def to_text(self, **kwargs):
        context = copy.deepcopy(self._context)
        context.update(kwargs)

        return "\n\n".join([node.to_text(**context) for node in self._nodes])

    def to_tex(self, full_doc = False, **kwargs):
        context = copy.deepcopy(self._context)
        context.update(kwargs)

        content = "\n\n".join([node.to_tex(**context) for node in self._nodes])

        if (full_doc):
            content = TEX_HEADER + "\n" + content + "\n" + TEX_FOOTER

        return content

    def to_html(self, full_doc = False, **kwargs):
        context = copy.deepcopy(self._context)
        context.update(kwargs)

        content = "\n\n".join([node.to_html(level = 1, **context) for node in self._nodes])
        content = f"<div class='document'>\n{content}\n</div>"

        if (full_doc):
            content = f"<html><body>{content}</body></html>"

        return content

    def to_pod(self, include_metadata = True, **kwargs):
        data = {
            "type": "document",
            "nodes": [node.to_pod(include_metadata = True, **kwargs) for node in self._nodes],
        }

        if (include_metadata):
            data["context"] = self._context

        return data

    def collect_file_paths(self, base_dir):
        paths = []

        for node in self._nodes:
            paths += node.collect_file_paths(base_dir)

        return paths

class BlockNode(ParseNode):
    def __init__(self, nodes):
        self._nodes = list(nodes)

    def to_markdown(self, **kwargs):
        return "\n".join([node.to_markdown(**kwargs) for node in self._nodes])

    def to_text(self, **kwargs):
        return "\n".join([node.to_text(**kwargs) for node in self._nodes])

    def to_tex(self, **kwargs):
        return "\n".join([node.to_tex(**kwargs) for node in self._nodes])

    def to_html(self, **kwargs):
        content = "\n".join([node.to_html(**kwargs) for node in self._nodes])
        return f"<div class='block' style='margin-bottom: 1em;'>\n{content}\n</div>"

    def to_pod(self, **kwargs):
        return {
            "type": "block",
            "nodes": [node.to_pod(**kwargs) for node in self._nodes],
        }

    def collect_file_paths(self, base_dir):
        paths = []

        for node in self._nodes:
            paths += node.collect_file_paths(base_dir)

        return paths

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

    def to_markdown(self, **kwargs):
        return f"![{self._text}]({self._link})"

    def to_text(self, **kwargs):
        return f"{self._text} ({self._link})"

    def to_tex(self, base_dir = '.', **kwargs):
        path = os.path.join(base_dir, self._link)
        return rf"\includegraphics[width=0.5\textwidth]{{{path}}}"

    def to_html(self, base_dir = '.', canvas_instance = None, **kwargs):
        if (re.match(r'^http(s)?://', self._link)):
            return f"<img src='{self._link}' alt='{self._text}' />"

        path = os.path.realpath(os.path.join(base_dir, self._link))

        if (canvas_instance is None):
            # If we are not uploading to canvas, do a base64 encode of the image.
            mime, content = encode_image(path)
            src = f"data:{mime};base64,{content}"
            return f"<img src='{src}' alt='{self._text}' />"

        # Canvas requires uploading the image, which should have been done via quizgen.converter.canvas.upload_canvas_files().

        file_id = canvas_instance.context.get('file_ids', {}).get(path)
        if (file_id is None):
            raise ValueError(f"Could not get canvas context file id of image '{path}'.")

        src = f"{canvas_instance.base_url}/courses/{canvas_instance.course_id}/files/{file_id}/preview"
        return f"<img src='{src}' alt='{self._text}' />"

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

    def to_tex(self, **kwargs):
        column_spec = "c" * self._width

        lines = [
            r'\begin{center}',
            r'    \begin{tabular}{ ' + column_spec + ' }',
        ]

        for row in self._rows:
            row = row.to_tex(width = self._width, **kwargs)
            lines.append(f"        {row}")

        lines += [
            r'    \end{tabular}',
            r'\end{center}',
            '',
        ]

        return "\n".join(lines)

    def to_html(self, **kwargs):
        table_style = ' ; '.join(HTML_TABLE_STYLE)

        lines = [
            f'<table style="{table_style}">',
        ]

        next_cell_style = None
        for row in self._rows:
            if (isinstance(row, TableSepNode)):
                next_cell_style = "border-top: 2px solid black;"
            else:
                lines.append(row.to_html(cell_style = next_cell_style, **kwargs))
                next_cell_style = None

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

class TableRowNode(ParseNode):
    def __init__(self, cells, head = False):
        self._cells = list(cells)
        self._head = head

    def to_markdown(self, **kwargs):
        return "| " + " | ".join([cell.to_markdown(**kwargs) for cell in self._cells]) + " |"

    def to_text(self, **kwargs):
        return "| " + " | ".join([cell.to_text(**kwargs) for cell in self._cells]) + " |"

    def to_tex(self, **kwargs):
        return " & ".join([cell.to_tex(**kwargs) for cell in self._cells]) + r' \\'

    def to_html(self, cell_style = None, **kwargs):
        tag = 'td'
        if (self._head):
            tag = 'th'

        cell_inline_style = "padding-left: 0.50em ; padding-right: 0.50em ; padding-bottom: 0.25em "
        if (cell_style is not None):
            cell_inline_style += (' ; ' + cell_style)

        lines = ['<tr>']

        for cell in self._cells:
            content = cell.to_html(**kwargs)
            content = f"<{tag} style='{cell_inline_style}' >{content}</{tag}>"
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

class TableSepNode(ParseNode):
    def __init__(self):
        pass

    def to_markdown(self, width = 1, **kwargs):
        return "|" + ("---|" * width)

    def to_text(self, width = 1, **kwargs):
        return "|" + ("---|" * width)

    def to_tex(self, **kwargs):
        return r'\hline \\'

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
        text = tex_escape(self._text)
        return rf"\textbf{{{text}}}"

    def to_html(self, **kwargs):
        text = html.escape(self._text)
        return f"<span><strong>{text}</strong></span>"

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
        if (bare and self._inline):
            return f"{self._text}"
        elif (bare and (not self._inline)):
            return f"\n{self._text}\n"
        elif ((not bare) and self._inline):
            return f"$ {self._text} $"
        else:
            return f"$$\n{self._text}\n$$"

    def to_tex(self, **kwargs):
        if (self._inline):
            return f"$ {self._text} $"

        return f"$$\n{self._text}\n$$"

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
