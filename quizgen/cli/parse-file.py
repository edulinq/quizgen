import argparse
import sys

import quizgen.parser

def run(args):
    document = quizgen.parser.parse_file(args.path)

    # TEST
    ''' TEST
    print("---")
    print(document)
    print("---")
    '''

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single file and output the results of the parse.")

    # TEST: Output as AST, TeX, HTML

    parser.add_argument('path',
        type = str,
        help = 'The path to parse.')

    return parser

def main():
    return run(_get_parser().parse_args())

if (__name__ == '__main__'):
    sys.exit(main())
