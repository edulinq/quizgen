import quizgen.parser.node
import quizgen.parser.style
import quizgen.parser.text

TEX_TEXT_TABLE_ALIGNMENT = {
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_LEFT: 'l',
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_CENTER: 'c',
    quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_RIGHT: 'r',
}

HTML_BORDER_SPEC = '1px solid black'

class TableNode(quizgen.parser.node.ParseNode):
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
        border_table = quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_BORDER_TABLE, quizgen.parser.style.DEFAULT_TABLE_BORDER_TABLE)
        border_cells = quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_BORDER_CELLS, quizgen.parser.style.DEFAULT_TABLE_BORDER_CELLS)
        alignment = quizgen.parser.style.get_alignment(style, quizgen.parser.style.KEY_TEXT_ALIGN, default_value = quizgen.parser.style.ALLOWED_VALUES_ALIGNMENT_CENTER)

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

        if (quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_BORDER_TABLE, quizgen.parser.style.DEFAULT_TABLE_BORDER_TABLE)):
            table_style.append("border: %s" % HTML_BORDER_SPEC)
        else:
            table_style.append('border-style: hidden')

        # HTML tables require extra encouragement to align.
        text_align = quizgen.parser.style.get_alignment(style, quizgen.parser.style.KEY_TEXT_ALIGN)
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

class TableRowNode(quizgen.parser.node.ParseNode):
    def __init__(self, cells, head = False):
        self._cells = list(cells)
        self._head = head

    def to_markdown(self, **kwargs):
        return "| " + " | ".join([cell.to_markdown(**kwargs) for cell in self._cells]) + " |"

    def to_text(self, **kwargs):
        return "| " + " | ".join([cell.to_text(**kwargs) for cell in self._cells]) + " |"

    def to_tex(self, style = {}, **kwargs):
        cells_text = [cell.to_tex(style = style, **kwargs) for cell in self._cells]

        if (self._head and quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_HEAD_BOLD, quizgen.parser.style.DEFAULT_TABLE_HEAD_BOLD)):
            cells_text = [quizgen.parser.text.BoldNode.bold_tex(text, escape = False) for text in cells_text]

        return " & ".join(cells_text) + r' \\'

    def to_html(self, extra_cell_style = {}, style = {}, **kwargs):
        tag = 'td'
        if (self._head):
            tag = 'th'

            weight = 'normal'
            if (quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_HEAD_BOLD, quizgen.parser.style.DEFAULT_TABLE_HEAD_BOLD)):
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
        height = max(1.0, float(style.get(quizgen.parser.style.KEY_TABLE_CELL_HEIGHT, quizgen.parser.style.DEFAULT_TABLE_CELL_HEIGHT)))
        vertical_padding = height - 1.0

        width = max(1.0, float(style.get(quizgen.parser.style.KEY_TABLE_CELL_WIDTH, quizgen.parser.style.DEFAULT_TABLE_CELL_WIDTH)))
        horizontal_padding = width - 1.0

        cell_style = {
            'padding-top': "%0.2fem" % (vertical_padding / 2),
            'padding-bottom': "%0.2fem" % (vertical_padding / 2),

            'padding-left': "%0.2fem" % (horizontal_padding / 2),
            'padding-right': "%0.2fem" % (horizontal_padding / 2),
        }

        if (quizgen.parser.style.get_boolean_style_key(style, quizgen.parser.style.KEY_TABLE_BORDER_CELLS, quizgen.parser.style.DEFAULT_TABLE_BORDER_CELLS)):
            cell_style['border'] = "%s" % (HTML_BORDER_SPEC)

        cell_style.update(extra_cell_style)

        return cell_style

class TableSepNode(quizgen.parser.node.ParseNode):
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
