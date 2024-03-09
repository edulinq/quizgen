import argparse
import os
import sys

import quizgen.converter.convert
import quizgen.constants
import quizgen.log
import quizgen.question.base

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    question = quizgen.question.base.Question.from_path(args.path)
    content = quizgen.converter.convert.convert_question(question, format = args.format,
            constructor_args = {'answer_key': args.answer_key})

    print(content)

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single quiz question (JSON file) and output the result in the specified format.")

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz question json file.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizgen.constants.FORMAT_JSON,
        choices = quizgen.converter.convert.SUPPORTED_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    parser.add_argument('--key', dest = 'answer_key',
        action = 'store_true', default = False,
        help = 'Generate an answer key instead of a blank quiz (default: %(default)s).')

    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
