import quizgen.parser.node

class ListNode(quizgen.parser.node.ParseNode):
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
