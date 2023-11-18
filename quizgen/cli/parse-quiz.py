import argparse
import os
import sys

import quizgen.constants
import quizgen.parser
import quizgen.quiz

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    quizzes = []
    if (os.path.isfile(args.path)):
        quizzes.append(quizgen.quiz.Quiz.from_path(args.path))
    else:
        quizzes += quizgen.quiz.parse_quiz_dir(args.path)

    if (len(quizzes) != 1):
        raise ValueError(f"Expected exactly one quiz, found {len(quizzes)}.")

    content = quizzes[0].to_format(args.format)
    print(content)

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single file and output the results of the parse.")

    parser.add_argument('path',
        type = str,
        help = 'The path to parse.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizgen.constants.DOC_FORMAT_JSON,
        choices = quizgen.constants.DOC_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    return parser

def main():
    return run(_get_parser().parse_args())

if (__name__ == '__main__'):
    sys.exit(main())
