"""
Create (and possibly upload) a quiz in the GradeScope format.
"""

import argparse
import datetime
import json
import logging
import os
import random
import string
import sys

import quizgen.converter.textemplate
import quizgen.latex
import quizgen.log
import quizgen.uploader.gradescope
import quizgen.util.file
import quizgen.quiz

OPTIONS_FILENAME = 'options.json'

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    if (args.upload):
        if ((args.course_id is None) or (args.user is None) or (args.password is None)):
            raise ValueError("If --upload is provided, then --course, --user, and --pass are all required.")

    if ((args.variants < 1) or (args.variants >= len(string.ascii_uppercase))):
        raise ValueError("Number of variants must be in [1, %d), found %d." % (len(string.ascii_uppercase), args.variants))

    quiz = quizgen.quiz.Quiz.from_path(args.path)

    out_dir = os.path.join(args.out_dir, quiz.title)
    os.makedirs(out_dir, exist_ok = True)

    logging.info("Writing generated output to '%s'.", out_dir)

    seed = args.seed
    if (seed is None):
        seed = random.randint(0, 2**64)

    options = {
        'create_time': datetime.datetime.now().isoformat(),
        'seed': seed,
        'out_dir': out_dir,
        'quiz': {
            'path': args.path,
            'title': quiz.title,
            'version': quiz.version,
        },
        'gradescope': {
            'upload': args.upload,
            'course': args.course_id,
            'rubric': args.rubric,
            'user': args.user,
        },
        'variants': {
            'count': args.variants,
            'titles': [],
            'ids': [],
        },
    }

    logging.info("Using seed %d.", seed)
    rng = random.Random(seed)

    gradescope_ids = []

    for i in range(args.variants):
        variant_id = None
        if (args.variants > 1):
            variant_id = string.ascii_uppercase[i]

        variant = quiz.create_variant(identifier = variant_id, seed = rng.randint(0, 2**64))
        out_path = os.path.join(out_dir, "%s.json" % (variant.title))
        quizgen.util.file.write(out_path, variant.to_json(include_docs = False))

        options['variants']['titles'].append(variant.title)

        if (args.upload):
            uploader = quizgen.uploader.gradescope.GradeScopeUploader(args.course_id, args.user, args.password,
                    force = args.force, rubric = args.rubric)
            gradescope_id, created = uploader.upload_quiz(variant, base_dir = out_dir)

            if (created):
                gradescope_ids.append(gradescope_id)

            options['variants']['ids'].append(gradescope_id)
        else:
            _make_pdf(variant, out_dir, False)
            options['variants']['ids'].append(None)

        title = variant.title

        # Always create an answer key.
        try:
            variant.title = "%s -- Answer Key" % (variant.title)
            _make_pdf(variant, out_dir, True)
        except Exception as ex:
            logging.warning("Failed to generate answer key for '%s'.", title)

        logging.info("Completed variant: '%s'.", title)

    # If there are multiple variants and all variants were created (non were skipped).
    if ((args.variants > 1) and (len(gradescope_ids) == args.variants)):
        uploader = quizgen.uploader.gradescope.GradeScopeUploader(args.course_id, args.user, args.password)
        uploader.create_assignment_group(quiz.title, gradescope_ids)
        logging.info("Created GradeScope Assignment Group: '%s'.", quiz.title)

    path = os.path.join(out_dir, OPTIONS_FILENAME)
    with open(path, 'w') as file:
        json.dump(options, file, indent = 4)

    return 0

def _make_pdf(variant, out_dir, is_key):
    converter = quizgen.converter.textemplate.TexTemplateConverter(answer_key = is_key)
    content = converter.convert_variant(variant)

    out_path = os.path.join(out_dir, "%s.tex" % (variant.title))
    quizgen.util.file.write(out_path, content)

    # Need to compile twice to get positioning.
    quizgen.latex.compile(out_path)
    quizgen.latex.compile(out_path)

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a quiz and potentially upload it to GradeScope.")

    parser.add_argument('path',
        type = str,
        help = 'The path to a quiz json file.')

    parser.add_argument('--variants', dest = 'variants',
        action = 'store', type = int, default = 1,
        help = 'The number of quiz variants to create (default: %(default)s).')

    parser.add_argument('--outdir', dest = 'out_dir',
        action = 'store', type = str, default = '.',
        help = 'The directory to put the quiz creation output (which will be another directory) (default: %(default)s).')

    parser.add_argument('--upload', dest = 'upload',
        action = 'store_true', default = False,
        help = 'Upload the quiz(zes) to GradeScope, requires --course, --user, and --pass (default: %(default)s).')

    parser.add_argument('--rubric', dest = 'rubric',
        action = 'store_true', default = False,
        help = 'Create an initial rubric for this assignment in GradeScope (default: %(default)s).')

    parser.add_argument('--course', dest = 'course_id',
        action = 'store', type = str,
        help = 'Course ID to upload the quiz under.')

    parser.add_argument('--user', dest = 'user',
        action = 'store', type = str,
        help = 'The user to authenticate as.')

    parser.add_argument('--pass', dest = 'password',
        action = 'store', type = str,
        help = 'The password to use.')

    parser.add_argument('--force', dest = 'force',
        action = 'store_true', default = False,
        help = 'Override (delete) any exiting quiz with the same name.')

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
