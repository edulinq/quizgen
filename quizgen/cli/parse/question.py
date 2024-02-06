import argparse
import json
import os
import sys

import quizgen.log
import quizgen.question

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    question = quizgen.question.Question.from_path(args.path)
    print(json.dumps(question.to_dict(), indent = 4))

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single quiz question (JSON file) and output the result as JSON.")

    parser.add_argument('path',
        type = str,
        help = 'The path to a quiz question json file.')

    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
