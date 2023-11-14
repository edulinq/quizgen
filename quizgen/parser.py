import abc
import json
import os

import lark
import lark.visitors

import quizgen.util.file

GRAMMAR = r'''
    document: [ block ( NEWLINE+ block )* NEWLINE* ]

    block: ( ( code_block | equation_block | table_block | text_line ) NEWLINE )+

    code_block: "```" NEWLINE? code_block_internal "```"
    ?code_block_internal: /.+?(?=```)/s

    equation_block: "$$" NEWLINE? equation_block_internal "$$"
    ?equation_block_internal: /.+?(?=\$\$)/s

    table_block: ( ( table_head | table_row | table_sep ) NEWLINE )+
    table_sep: /\|---\|.*/
    table_row: "|" table_cell+
    table_head: "|-" table_cell+
    table_cell: text_line "|"

    text_line: ( inline_code | inline_equation | inline_italics | inline_bold | inline_link | inline_image | inline_text )+

    inline_link: INLINE_LINK_TEXT INLINE_LINK_LINK
    inline_image: "!" INLINE_LINK_TEXT INLINE_LINK_LINK
    inline_code: INLINE_CODE
    inline_equation: INLINE_EQUATION
    inline_italics: INLINE_ITALICS
    inline_bold: INLINE_BOLD
    inline_text: ( ESC_CHAR | NON_ESC_TEXT )+

    _ESCAPE_INTERNAL: /.+?/ /(?<!\\)(\\\\)*?/

    INLINE_CODE: "`" _ESCAPE_INTERNAL "`"
    INLINE_EQUATION: "$" _ESCAPE_INTERNAL "$"
    INLINE_ITALICS: "*" _ESCAPE_INTERNAL "*"
    INLINE_BOLD: "**" _ESCAPE_INTERNAL "**"
    INLINE_LINK_TEXT: "[" _ESCAPE_INTERNAL "]"
    INLINE_LINK_LINK: "(" _ESCAPE_INTERNAL ")"

    NON_ESC_TEXT: NON_ESC_CHAR+
    NON_ESC_CHAR: /[^\n\\`|\*\$\-\[!]/x
    ESC_CHAR: "\\\\"
            | "\\-"
            | "\\*"
            | "\\|"
            | "\\$"
            | "\\["
            | "\\!"
            | "\\`"

    NEWLINE: /\n/
'''

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

    def inline_text(self, text):
        return NormalTextNode(''.join(text))

    def ESC_CHAR(self, text):
        # Remove the backslash.
        return text[1:]

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
        return CodeNode(text, inline = True)

    def inline_equation(self, text):
        # Strip off the dollar signs.
        text = str(text[0])[1:-1].strip()
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

    def inline_link(self, contents):
        text = str(contents[0])[1:-1]
        link = str(contents[1])[1:-1]

        return LinkNode(text, link)

    def inline_image(self, contents):
        text = str(contents[0])[1:-1]
        link = str(contents[1])[1:-1]

        return ImageNode(text, link)

    def NON_ESC_TEXT(self, text):
        return str(text)

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
    def to_pod(self):
        """
        Get a "Plain Old Data" representation of the node."
        This representation should be convertable to JSON."
        """

        pass

    def to_json(self, indent = 4):
        return json.dumps(self.to_pod(), indent = indent)

class DocumentNode(ParseNode):
    def __init__(self, nodes):
        self._nodes = list(nodes)

    def to_markdown(self, **kwargs):
        return "\n\n".join([node.to_markdown() for node in self._nodes])

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
        return {
            "type": "document",
            "nodes": [node.to_pod() for node in self._nodes],
        }

class BlockNode(ParseNode):
    def __init__(self, nodes):
        self._nodes = list(nodes)

    def to_markdown(self, **kwargs):
        return "\n".join([node.to_markdown() for node in self._nodes])

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
        return {
            "type": "block",
            "nodes": [node.to_pod() for node in self._nodes],
        }

class LinkNode(ParseNode):
    def __init__(self, text, link):
        self._text = text
        self._link = link

    def to_markdown(self, **kwargs):
        return f"[{self._text}]({self._link})"

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
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

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
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
        return "\n".join([row.to_markdown(width = self._width) for row in self._rows]) + "\n"

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
        return {
            "type": "table",
            "rows": [row.to_pod() for row in self._rows],
        }

class TableRowNode(ParseNode):
    def __init__(self, cells, head = False):
        self._cells = list(cells)
        self._head = head

    def to_markdown(self, **kwargs):
        return "| " + " | ".join([cell.to_markdown() for cell in self._cells]) + " |"

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
        return {
            "type": "table-row",
            "head": self._head,
            "cells": [cell.to_pod() for cell in self._cells],
        }

    def __len__(self):
        return len(self._cells)

class TableSepNode(ParseNode):
    def __init__(self):
        pass

    def to_markdown(self, width = 1, **kwargs):
        return "|" + ("---|" * width)

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
        return {
            "type": "table-sep",
        }

    def __len__(self):
        return 1

class TextNode(ParseNode):
    def __init__(self, nodes):
        self._nodes = list(nodes)

    def to_markdown(self, **kwargs):
        # TEST: Need space?
        return "".join([node.to_markdown() for node in self._nodes])

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
        return {
            "type": "text",
            "nodes": [node.to_pod() for node in self._nodes],
        }

    def trim(self):
        """
        Trim the whitespace off the edges of this node.
        """

        self._nodes[0]._text = self._nodes[0]._text.lstrip()
        self._nodes[-1]._text = self._nodes[-1]._text.rstrip()

        return self

class NormalTextNode(ParseNode):
    def __init__(self, text):
        self._text = text

    def to_markdown(self, **kwargs):
        return self._text

    def to_tex(self, **kwargs):
        return self._text

    def to_html(self, **kwargs):
        return f"<span>self._text</span>"

    def to_pod(self):
        return {
            "type": "normal_text",
            "text": self._text,
        }

class ItalicsNode(ParseNode):
    def __init__(self, text):
        self._text = text

    def to_markdown(self, **kwargs):
        return f"*{self._text}*"

    def to_tex(self, **kwargs):
        return f"\textit{self._text}"

    def to_html(self, **kwargs):
        return f"<emph>{self._text}</emph>"

    def to_pod(self):
        return {
            "type": "italics_text",
            "text": self._text,
        }

class BoldNode(ParseNode):
    def __init__(self, text):
        self._text = text

    def to_markdown(self, **kwargs):
        return f"**{self._text}**"

    def to_tex(self, **kwargs):
        return f"\textbf{self._text}"

    def to_html(self, **kwargs):
        return f"<strong>{self._text}</strong>"

    def to_pod(self):
        return {
            "type": "bold_text",
            "text": self._text,
        }

class CodeNode(ParseNode):
    def __init__(self, text, inline = False):
        self._text = text
        self._inline = inline

    def to_markdown(self, **kwargs):
        if (self._inline):
            return f"`{self._text}`"

        return f"```\n{self._text}\n```"

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
        return {
            "type": "code",
            "inline": self._inline,
            "text": self._text,
        }

class EquationNode(ParseNode):
    def __init__(self, text, inline = False):
        self._text = text
        self._inline = inline

    def to_markdown(self, **kwargs):
        if (self._inline):
            return f"$ {self._text} $"

        return f"$$\n{self._text}\n$$"

    def to_tex(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_html(self, **kwargs):
        # TEST
        raise NotImplementedError()

    def to_pod(self):
        return {
            "type": "equation",
            "inline": self._inline,
            "text": self._text,
        }

def clean_text(text):
    # Remove carriage returns.
    text = text.replace("\r", '')

    # Trim whitespace.
    text = text.strip();

    # Replace the final newline and add one additional one (for tables).
    text += "\n\n"

    return text

def parse_file(path):
    if (not os.path.isfile(path)):
        raise ValueError(f"Path to parse ('{path}') is not a file.")

    text = quizgen.util.file.read(path)
    text = clean_text(text)

    parser = lark.Lark(GRAMMAR, start = 'document')
    ast = parser.parse(text)

    document = DocTransformer().transform(ast)

    return document
