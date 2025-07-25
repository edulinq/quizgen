import os
import sys

import quizcomp.args
import quizcomp.downloader.canvas

# TEST - This shouldn't be defaulted to UCSC.
DEFAULT_BASE_URL = 'https://canvas.ucsc.edu'

def run(args):
    # TEST - Check output dir.

    quizcomp.downloader.canvas.download_quiz_question(args.base_url, args.course_id, args.token, args.quiz, args.question)

    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        "Download a quiz question from Canvas.")

    parser.add_argument('quiz', metavar = '<quiz>',
        type = str,
        help = 'The id or name of the target Canvas quiz.')

    parser.add_argument('question', metavar = '<question>',
        type = str,
        help = 'The id or name of the target Canvas question.')

    parser.add_argument('--course', dest = 'course_id',
        action = 'store', type = str, required = True,
        help = 'Course ID to upload the quiz under.')

    parser.add_argument('--url', dest = 'base_url',
        action = 'store', type = str, default = DEFAULT_BASE_URL,
        help = 'The base URL for the Canvas instance (default: %(default)s).')

    parser.add_argument('--token', dest = 'token',
        action = 'store', type = str, required = True,
        help = 'The authentication token to use with Canvas.')

    # TEST
    parser.add_argument('--force', dest = 'force',
        action = 'store_true', default = False,
        help = 'Override (delete) any exiting quiz with the same name.')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
