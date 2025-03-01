import os
import sys

import quizgen.args
import quizgen.converter.qti
import quizgen.quiz
import quizgen.util.cli

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    quiz = quizgen.quiz.Quiz.from_path(args.path)

    out_path = quizgen.util.cli.resolve_out_arg(args.out, f'{quiz.title}.qti.zip')

    converter = quizgen.converter.qti.QTITemplateConverter(canvas = args.canvas)
    converter.convert_quiz(quiz, out_path = out_path)

    return 0

def _get_parser():
    parser = quizgen.args.Parser(description =
        "Parse a quiz and upload the quiz to Canvas.")

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz JSON file.')

    parser.add_argument('--canvas', dest = 'canvas',
        action = 'store_true', default = False,
        help = 'Create the QTI with Canvas-specific tweaks (default: %(default)s).')

    quizgen.util.cli.add_out_arg(parser, '<title>.qti.zip')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
