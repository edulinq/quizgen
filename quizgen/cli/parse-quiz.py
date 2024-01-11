import argparse
import os
import sys

import quizgen.converter.gstemplate
import quizgen.converter.htmltemplate
import quizgen.converter.textemplate
import quizgen.constants
import quizgen.parser
import quizgen.quiz

SUPPORTED_FORMATS = [
    quizgen.constants.DOC_FORMAT_GRADESCOPE,
    quizgen.constants.DOC_FORMAT_HTML,
    quizgen.constants.DOC_FORMAT_JSON,
    quizgen.constants.DOC_FORMAT_TEX,
]

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    quiz = quizgen.quiz.Quiz.from_path(args.path, flatten_groups = args.flatten_groups)
    variant = quiz.create_variant(all_questions = args.flatten_groups)

    if (args.format == quizgen.constants.DOC_FORMAT_JSON):
        content = variant.to_json()
    elif (args.format == quizgen.constants.DOC_FORMAT_HTML):
        converter = quizgen.converter.htmltemplate.HTMLTemplateConverter(answer_key = args.answer_key)
        content = converter.convert_quiz(variant)
    elif (args.format == quizgen.constants.DOC_FORMAT_TEX):
        converter = quizgen.converter.textemplate.TexTemplateConverter(answer_key = args.answer_key)
        content = converter.convert_quiz(variant)
    elif (args.format == quizgen.constants.DOC_FORMAT_GRADESCOPE):
        converter = quizgen.converter.gstemplate.GradeScopeTemplateConverter(answer_key = args.answer_key)
        content = converter.convert_quiz(variant)
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
        choices = SUPPORTED_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    parser.add_argument('--key', dest = 'answer_key',
        action = 'store_true', default = False,
        help = 'Generate an answer key instead of a blank quiz (default: %(default)s).')

    parser.add_argument('--flatten-groups', dest = 'flatten_groups',
        action = 'store_true', default = False,
        help = 'Flatten question groups with multiple questions to multiple groups with a single question (default: %(default)s).')

    return parser

def main():
    return run(_get_parser().parse_args())

if (__name__ == '__main__'):
    sys.exit(main())
