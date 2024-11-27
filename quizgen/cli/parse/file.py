import argparse
import sys

import quizgen.constants
import quizgen.log
import quizgen.parser.public

def run(args):
    document = quizgen.parser.public.parse_file(args.path).document

    content = document.to_format(args.format, pretty = True)
    print(content)

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single file and output the results of the parse.")

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to parse.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizgen.constants.FORMAT_JSON,
        choices = quizgen.constants.PARSER_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
