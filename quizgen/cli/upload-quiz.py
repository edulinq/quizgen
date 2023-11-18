import argparse
import os
import sys

import quizgen.canvas
import quizgen.quiz

DEFAULT_BASE_URL = 'https://canvas.ucsc.edu'

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

    quizgen.canvas.upload_quiz(quizzes[0], quizgen.canvas.InstanceInfo(args.base_url, args.course_id, args.token))

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single file and output the results of the parse.")

    parser.add_argument('path',
        type = str,
        help = 'The path to parse.')

    parser.add_argument('--course', dest = 'course_id',
        action = 'store', type = str, required = True,
        help = 'Course ID to upload the quiz under.')

    parser.add_argument('--url', dest = 'base_url',
        action = 'store', type = str, default = DEFAULT_BASE_URL,
        help = 'The base URL for the Canvas instance (default: %(default)s).')

    parser.add_argument('--token', dest = 'token',
        action = 'store', type = str, required = True,
        help = 'The authentication token to use with Canvas.')

    return parser

def main():
    return run(_get_parser().parse_args())

if (__name__ == '__main__'):
    sys.exit(main())
