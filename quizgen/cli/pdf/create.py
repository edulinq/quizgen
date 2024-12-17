"""
Create a PDF quiz.
"""

import sys

import quizgen.args
import quizgen.pdf

def run(args):
    quizgen.pdf.make_with_args(args)
    return 0

def _get_parser():
    parser = quizgen.args.Parser(description =
        "Create a PDF quiz.")

    quizgen.pdf.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
