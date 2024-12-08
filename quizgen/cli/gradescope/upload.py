"""
Create and upload a GradeScope PDF quiz.
"""

import argparse
import json
import logging
import os
import sys

import quizgen.log
import quizgen.pdf
import quizgen.uploader.gradescope
import quizgen.util.dirent

def run(args):
    quiz, variants, options = quizgen.pdf.make_with_args(args, write_options = False)
    out_dir = options['out_dir']

    options['gradescope'] = {
        'course': args.course_id,
        'rubric': args.rubric,
        'user': args.user,
    }

    gradescope_ids = []

    for i in range(len(variants)):
        variant = variants[i]

        uploader = quizgen.uploader.gradescope.GradeScopeUploader(args.course_id, args.user, args.password,
                force = args.force, rubric = args.rubric)
        gradescope_id, created = uploader.upload_quiz(variant, base_dir = out_dir)

        options['variants'][i]['gradescope_id'] = gradescope_id

    # If there are multiple variants and all variants were created (non were skipped).
    if (len(variants) > 1):
        ids = [variants_data['gradescope_id'] for variants_data in options['variants']]

        uploader = quizgen.uploader.gradescope.GradeScopeUploader(args.course_id, args.user, args.password)
        uploader.create_assignment_group(quiz.title, ids)
        logging.info("Created GradeScope Assignment Group: '%s'.", quiz.title)

    path = os.path.join(out_dir, quizgen.pdf.OPTIONS_FILENAME)
    with open(path, 'w') as file:
        json.dump(options, file, indent = 4)

    return 0

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Create and upload a GradeScope PDF quiz.")

    quizgen.pdf.set_cli_args(parser)

    parser.add_argument('--rubric', dest = 'rubric',
        action = 'store_true', default = False,
        help = 'Create an initial rubric for this assignment in GradeScope (default: %(default)s).')

    parser.add_argument('--course', dest = 'course_id',
        action = 'store', type = str, required = True,
        help = 'Course ID to upload the quiz under.')

    parser.add_argument('--user', dest = 'user',
        action = 'store', type = str, required = True,
        help = 'The user to authenticate as.')

    parser.add_argument('--pass', dest = 'password',
        action = 'store', type = str, required = True,
        help = 'The password to use.')

    parser.add_argument('--force', dest = 'force',
        action = 'store_true', default = False,
        help = 'Override (delete) any exiting quiz with the same name.')

    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
