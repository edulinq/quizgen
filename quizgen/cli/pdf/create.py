"""
Create a PDF quiz.
"""

import argparse
import sys

import quizgen.log
import quizgen.pdf

def run(args):
    quizgen.pdf.make_with_args(args)
    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Create a PDF quiz.")

    quizgen.pdf.set_cli_args(parser)
    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
