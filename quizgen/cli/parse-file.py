import argparse
import json
import sys

import quizgen.parser

FORMAT_HTML = 'html'
FORMAT_JSON = 'json'
FORMAT_MD = 'md'
FORMAT_TEX = 'tex'
FORMATS = [FORMAT_HTML, FORMAT_JSON, FORMAT_MD, FORMAT_TEX]

def run(args):
    document = quizgen.parser.parse_file(args.path)

    content = ""
    if (args.format == FORMAT_HTML):
        content = document.to_html(full_doc = args.full_doc)
    elif (args.format == FORMAT_JSON):
        content = document.to_json()
    elif (args.format == FORMAT_MD):
        content = document.to_markdown()
    elif (args.format == FORMAT_TEX):
        content = document.to_tex(full_doc = args.full_doc)
    else:
        raise ValueError(f"Unknown format '{args.format}'.")

    print(content)

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single file and output the results of the parse.")

    parser.add_argument('path',
        type = str,
        help = 'The path to parse.')

    parser.add_argument('--format',
        action = 'store', type = str, default = FORMAT_JSON,
        choices = FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    parser.add_argument('--full', dest = 'full_doc',
        action = 'store_true', default = False,
        help = 'Treat the output as a fill document instead of just a snippet, e.g. TeX will output a full document (default: %(default)s)')

    return parser

def main():
    return run(_get_parser().parse_args())

if (__name__ == '__main__'):
    sys.exit(main())
