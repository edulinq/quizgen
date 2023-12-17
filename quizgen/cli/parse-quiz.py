import argparse
import os
import sys

import quizgen.converter.textemplate
import quizgen.constants
import quizgen.parser
import quizgen.quiz

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    quiz = quizgen.quiz.Quiz.from_path(args.path)

    if (args.format == quizgen.constants.DOC_FORMAT_JSON):
        content = quiz.to_json()
    elif (args.format == quizgen.constants.DOC_FORMAT_TEX):
        converter = quizgen.converter.textemplate.TexTemplateConverter()
        content = converter.convert_quiz(quiz)
    else:
        raise NotImplementedError("Quiz output format '%s' is not currently supported." % (args.format))

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
        choices = quizgen.constants.DOC_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    return parser

def main():
    return run(_get_parser().parse_args())

if (__name__ == '__main__'):
    sys.exit(main())
