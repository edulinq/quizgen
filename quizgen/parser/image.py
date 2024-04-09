import base64
import os
import re

import quizgen.parser.node
import quizgen.parser.style

ENCODING = 'utf-8'

class ImageNode(quizgen.parser.node.ParseNode):
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
            mime, content = _encode_image(path)
            attr['src'] = f"data:{mime};base64,{content}"

        content = []
        for (key, value) in sorted(attr.items()):
            value = str(value).replace("'", r"\'")
            content.append("%s='%s'" % (key, value))

        return "<img %s />" % (' '.join(content))

    def _get_width(self, style):
        width = style.get(quizgen.parser.style.KEY_IMAGE_WIDTH, None)
        if (width is None):
            width = quizgen.parser.style.DEFAULT_IMAGE_WIDTH

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

def _encode_image(path):
    ext = os.path.splitext(path)[-1].lower()
    mime = f"image/{ext}"

    with open(path, 'rb') as file:
        data = file.read()

    content = base64.standard_b64encode(data)
    return mime, content.decode(ENCODING)
