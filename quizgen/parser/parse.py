import json5
import lark
import lark.visitors

import quizgen.parser.image
import quizgen.parser.list
import quizgen.parser.node
import quizgen.parser.table
import quizgen.parser.text

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

# Module-shared parser/transformer.
_parser = None
_transformer = None

def _get_parser():
    global _parser
    global _transformer

    if (_parser is None):
        _parser = lark.Lark(GRAMMAR, start = 'document')
        _transformer = _DocTransformer()

    return _parser, _transformer

class _DocTransformer(lark.Transformer):
    def document(self, blocks):
        return quizgen.parser.node.DocumentNode(blocks[0])

    def blocks(self, blocks):
        return blocks

    def block(self, nodes):
        # Lift blocks and style up.
        if ((len(nodes) == 1) and isinstance(nodes[0], (quizgen.parser.node.BlockNode, quizgen.parser.node.StyleNode))):
            return nodes[0]

        return quizgen.parser.node.BlockNode(nodes)

    def explicit_block(self, nodes):
        return quizgen.parser.node.BlockNode(nodes[0])

    def style_block(self, text):
        text = '{' + text[0].strip("\n") + '}'
        try:
            data = json5.loads(text)
        except Exception as ex:
            raise ValueError("Style is not valid JSON.") from ex

        return quizgen.parser.node.StyleNode(data)

    def code_block(self, text):
        # Trim any newlines.
        text = text[0].strip("\n")
        return quizgen.parser.text.CodeNode(text, inline = False)

    def equation_block(self, text):
        # Trim any newlines.
        text = text[0].strip()
        return quizgen.parser.text.EquationNode(text, inline = False)

    def text_line(self, nodes):
        return quizgen.parser.text.TextNode(nodes)

    def inline_comment(self, text):
        return quizgen.parser.text.CommentNode(str(text[1]).strip())

    def inline_text(self, text):
        return quizgen.parser.text.NormalTextNode(''.join(text))

    def inline_linebreak(self, _):
        return quizgen.parser.text.LinebreakNode()

    def inline_answer_reference(self, text):
        return quizgen.parser.text.AnswerReferenceNode(str(text[0]))

    def inline_italics(self, text):
        # Strip off the asterisks.
        text = str(text[0])[1:-1]
        return quizgen.parser.text.ItalicsNode(text)

    def inline_bold(self, text):
        # Strip off the asterisks.
        text = str(text[0])[2:-2]
        return quizgen.parser.text.BoldNode(text)

    def inline_code(self, text):
        # Strip off the backticks.
        text = str(text[0])[1:-1]

        # Replace any escaped backticks.
        text = text.replace(r'\`', '`')

        return quizgen.parser.text.CodeNode(text, inline = True)

    def inline_equation(self, text):
        # Strip off the dollar signs.
        text = str(text[0])[1:-1].strip()

        # Replace any escaped dollar signs.
        text = text.replace(r'\$', '$')

        return quizgen.parser.text.EquationNode(text, inline = True)

    def table_block(self, rows):
        return quizgen.parser.table.TableNode(rows)

    def table_row(self, cells):
        return quizgen.parser.table.TableRowNode(cells, head = False)

    def table_head(self, cells):
        return quizgen.parser.table.TableRowNode(cells, head = True)

    def table_sep(self, cells):
        return quizgen.parser.table.TableSepNode()

    def table_cell(self, cell):
        return cell[0].trim()

    def list_block(self, items):
        return quizgen.parser.list.ListNode([item.trim() for item in items])

    def inline_link(self, contents):
        # Remove the surrounding characters, strip it, and replace escaped end markers.
        text = str(contents[0])[1:-1].strip().replace(r'\]', ']')
        link = str(contents[1])[1:-1].strip().replace(r'\)', ')')

        return quizgen.parser.text.LinkNode(text, link)

    def inline_image(self, contents):
        text = str(contents[0])[1:-1].strip()
        link = str(contents[1])[1:-1].strip()

        return quizgen.parser.image.ImageNode(text, link)

    def NON_ESC_TEXT(self, text):
        return str(text)

    def ESC_CHAR(self, text):
        # Remove the backslash.
        return text[1:]

    def LIST_ITEM_START(self, token):
        return lark.visitors.Discard

    def NEWLINE(self, token):
        return lark.visitors.Discard

def _clean_text(text):
    # Remove carriage returns.
    text = text.replace("\r", '')

    # Trim whitespace.
    text = text.strip();

    # Replace the final newline and add one additional one (for tables).
    text += "\n\n"

    return text

# Returns (transformed text, document).
def _parse_text(text, base_dir = '.'):
    # Special case for empty documents.
    if (text.strip() == ''):
        return ('', quizgen.parser.node.DocumentNode([]))

    text = _clean_text(text)

    parser, transformer = _get_parser()

    ast = parser.parse(text)
    document = transformer.transform(ast)
    document.set_base_dir(base_dir)

    return (text.strip(), document)
