import argparse
import os
import random
import sys

import quizgen.converter.convert
import quizgen.constants
import quizgen.log
import quizgen.quiz

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    seed = args.seed
    if (seed is None):
        seed = random.randint(0, 2**64)

    quiz = quizgen.quiz.Quiz.from_path(args.path, flatten_groups = args.flatten_groups)
    variant = quiz.create_variant(all_questions = args.flatten_groups, seed = seed)
    content = quizgen.converter.convert.convert_variant(variant, format = args.format,
            constructor_args = {'answer_key': args.answer_key})

    print(content)

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single quiz and output the results of the parse.")

    parser.add_argument('path',
        type = str,
        help = 'The path to a quiz json file.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizgen.constants.DOC_FORMAT_JSON,
        choices = quizgen.converter.convert.SUPPORTED_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    parser.add_argument('--key', dest = 'answer_key',
        action = 'store_true', default = False,
        help = 'Generate an answer key instead of a blank quiz (default: %(default)s).')

    parser.add_argument('--flatten-groups', dest = 'flatten_groups',
        action = 'store_true', default = False,
        help = 'Flatten question groups with multiple questions to multiple groups with a single question (default: %(default)s).')

    parser.add_argument('--seed', dest = 'seed',
        action = 'store', type = int, default = None,
        help = 'The random seed to use (defaults to a random seed).')

    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
