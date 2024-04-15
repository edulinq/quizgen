import os

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TYPES_DIR = os.path.join(THIS_DIR, '..', 'data', 'types')

METATYPE_FILENAME = 'jtype.json'
METATYPE_PATH = os.path.join(TYPES_DIR, METATYPE_FILENAME)
