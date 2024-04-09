"""
Style constants and base functionality.
"""

KEY_CONTENT_ALIGN = 'content-align'
KEY_FONT_SIZE = 'font-size'
KEY_IMAGE_WIDTH = 'image-width'
KEY_TABLE_BORDER_CELLS = 'table-border-cells'
KEY_TABLE_BORDER_TABLE = 'table-border-table'
KEY_TABLE_CELL_HEIGHT = 'table-cell-height'
KEY_TABLE_CELL_WIDTH = 'table-cell-width'
KEY_TABLE_HEAD_BOLD = 'table-head-bold'
KEY_TEXT_ALIGN = 'text-align'

DEFAULT_IMAGE_WIDTH = 1.0
DEFAULT_TABLE_BORDER_CELLS = False
DEFAULT_TABLE_BORDER_TABLE = False
DEFAULT_TABLE_CELL_HEIGHT = 1.5
DEFAULT_TABLE_CELL_WIDTH = 1.5
DEFAULT_TABLE_HEAD_BOLD = True

ALLOWED_VALUES_ALIGNMENT_LEFT = 'left'
ALLOWED_VALUES_ALIGNMENT_CENTER = 'center'
ALLOWED_VALUES_ALIGNMENT_RIGHT = 'right'
ALLOWED_VALUES_ALIGNMENT = [
    ALLOWED_VALUES_ALIGNMENT_LEFT,
    ALLOWED_VALUES_ALIGNMENT_CENTER,
    ALLOWED_VALUES_ALIGNMENT_RIGHT
]

def get_alignment(style, key, default_value = None):
    alignment = style.get(key, None)
    if (alignment is None):
        return default_value

    alignment = str(alignment).lower()
    if (alignment not in ALLOWED_VALUES_ALIGNMENT):
        raise ValueError("Unknown value for '%s' style key '%s'. Allowed values: '%s'." % (key, alignment, ALLOWED_VALUES_ALIGNMENT))

    return alignment

def get_boolean_style_key(style, key, default_value = None):
    value = style.get(key, default_value)
    if (value is None):
        return default_value

    return (value is True)
