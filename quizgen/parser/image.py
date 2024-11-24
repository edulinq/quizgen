import base64
import os
import re

import quizgen.constants
import quizgen.parser.common
import quizgen.parser.style

# TEST - Canvas (html) images require special handling.

# Cache the results of any image callbacks using (original src, base dir) as the key.
_callback_cache = {}

def render(format, tokens, idx, options, env):
    context = env.get(quizgen.parser.common.CONTEXT_ENV_KEY, {})
    style = context.get('style', {})

    src = tokens[idx].attrGet('src')
    base_dir = context.get(quizgen.parser.common.BASE_DIR_KEY, '.')
    callback = context.get(quizgen.parser.common.CONTEXT_KEY_IMAGE_CALLBACK, None)

    src = _handle_callback(callback, src, base_dir)
    tokens[idx].attrSet('src', src)

    if (format == quizgen.constants.FORMAT_HTML):
        _render_html(context, style, base_dir, tokens, idx, options, env)

def _render_html(context, style, base_dir, tokens, idx, options, env):
    # Set width.
    width_float = quizgen.parser.style.get_image_width(style)
    tokens[idx].attrSet('width', "%0.2f%%" % (width_float * 100.0))

    src = tokens[idx].attrGet('src')
    path = os.path.realpath(os.path.join(base_dir, src))
    force_raw_image_src = context.get(quizgen.parser.common.CONTEXT_KEY_FORCE_RAW_IMAGE_SRC, False)

    if (force_raw_image_src or re.match(r'^http(s)?://', src)):
        # Do not further modify the src if it is a http URL or we are explicitly directed not to.
        pass
    else:
        # Otherwise, do a base64 encoding of the image and embed it.
        mime, content = _encode_image(path)
        tokens[idx].attrSet('src', f"data:{mime};base64,{content}")

def _handle_callback(callback, original_src, base_dir):
    key = (original_src, base_dir)

    computed_src = _callback_cache.get(key, None)
    if (computed_src is not None):
        return computed_src

    if (callback is None):
        return original_src

    computed_src = callback(original_src, base_dir)
    _callback_cache[key] = computed_src

    return computed_src

def _encode_image(path):
    ext = os.path.splitext(path)[-1].lower()
    mime = f"image/{ext}"

    with open(path, 'rb') as file:
        data = file.read()

    content = base64.standard_b64encode(data)
    return mime, content.decode(quizgen.parser.common.ENCODING)
