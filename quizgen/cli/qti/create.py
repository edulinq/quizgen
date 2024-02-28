import argparse
import os
import sys

import quizgen.converter.qtitemplate
import quizgen.log
import quizgen.quiz

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    quiz = quizgen.quiz.Quiz.from_path(args.path)

    converter = quizgen.converter.qtitemplate.QTITemplateConverter(canvas = args.canvas)
    converter.convert_quiz(quiz, out_dir = args.out_dir)

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a quiz and upload the quiz to Canvas.")

    parser.add_argument('path',
        type = str,
        help = 'The path to a quiz json file.')

    parser.add_argument('--canvas', dest = 'canvas',
        action = 'store_true', default = False,
        help = 'Create the QTI with Canvas-specific tweaks (default: %(default)s).')

    parser.add_argument('--outdir', dest = 'out_dir',
        action = 'store', type = str, default = '.',
        help = 'The directory to put the quiz creation output (default: %(default)s).')

    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
