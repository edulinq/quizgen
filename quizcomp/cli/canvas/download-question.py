import os
import sys

import quizcomp.args
import quizcomp.downloader.canvas
import quizcomp.util.dirent

DEFAULT_BASE_URL = 'https://canvas.ucsc.edu'

def run(args):
    # Default the out dir to question's query.
    if (args.out_dir is None):
        args.out_dir = args.question

    # Clean the out dir.
    args.out_dir = os.path.realpath(args.out_dir)

    if ((not args.force) and os.path.exists(args.out_dir)):
        print(f"Output path for question already exists: '{args.out_dir}'.")
        return 1

    # Remove any existing out dir (as long as it is not the CWD).
    if (args.out_dir != os.path.realpath('.')):
        quizcomp.util.dirent.remove_dirent(args.out_dir)

    question = quizcomp.downloader.canvas.download_quiz_question(args.base_url, args.course_id, args.token, args.quiz, args.question)
    question.write(out_dir = args.out_dir, split_prompt = True)

    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        "Download a quiz question from Canvas.")

    parser.add_argument('quiz', metavar = '<quiz>',
        type = str,
        help = 'The query (id or name) of the target Canvas quiz.')

    parser.add_argument('question', metavar = '<question>',
        type = str,
        help = 'The query (id or name) of the target Canvas question.')

    parser.add_argument('--course', dest = 'course_id',
        action = 'store', type = str, required = True,
        help = 'Course ID to upload the quiz under.')

    parser.add_argument('--url', dest = 'base_url',
        action = 'store', type = str, default = DEFAULT_BASE_URL,
        help = 'The base URL for the Canvas instance (default: %(default)s).')

    parser.add_argument('--token', dest = 'token',
        action = 'store', type = str, required = True,
        help = 'The authentication token to use with Canvas.')

    parser.add_argument('--out', dest = 'out_dir',
        action = 'store', type = str, default = None,
        help = "The output question directory, defaults to a directory in the CWD named with the question's query.")

    parser.add_argument('--force', dest = 'force',
        action = 'store_true', default = False,
        help = 'Override (delete) any exiting output directory.')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
