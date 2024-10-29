import html

import quizgen.katex
import quizgen.parser.node

TEX_REPLACEMENTS = {
    # Specially handle braces and slashes to avoid clobbering other replacements.
    '{': 'ZZZzzz  OPEN BRACE REPLACEMENT  zzzZZZ',
    '}': 'ZZZzzz  CLOSE BRACE REPLACEMENT  zzzZZZ',
    '\\': 'ZZZzzz  BACKSLASH REPLACEMENT  zzzZZZ',

    '|': '\\textbar{}',
    '$': '\\$',
    '#': '\\#',
    '%': '\\%',
    '^': '\\^',
    '_': '\\_',
    'π': '$\\pi$',
    '`': '\\`{}',

    'ZZZzzz  OPEN BRACE REPLACEMENT  zzzZZZ': '\\{',
    'ZZZzzz  CLOSE BRACE REPLACEMENT  zzzZZZ': '\\}',
    'ZZZzzz  BACKSLASH REPLACEMENT  zzzZZZ': '\\textbackslash{}',
}

VERB_CHARACTERS = ['|', '!', '@', '#', '$', '^', '&', '-', '_', '=', '+']

class TextNode(quizgen.parser.node.ParseNode):
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

class LinebreakNode(quizgen.parser.node.ParseNode):
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

class LinkNode(quizgen.parser.node.ParseNode):
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

class BaseTextNode(quizgen.parser.node.ParseNode):
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
        if (escape):
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

def tex_escape(text):
    """
    Prepare normal text for tex.
    """

    for key, value in TEX_REPLACEMENTS.items():
        text = text.replace(key, value)

    return text
