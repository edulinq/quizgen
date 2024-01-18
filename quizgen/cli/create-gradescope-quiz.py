"""
Create (and possibly upload) a quiz in the GradeScope format.
"""

import argparse
import os
import string
import sys

import quizgen.converter.gradescope
import quizgen.converter.gstemplate
import quizgen.latex
import quizgen.util.file
import quizgen.quiz

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

    print("Writing generated output to '%s'." % (out_dir))

    gradescope_ids = []

    for i in range(args.variants):
        variant_id = None
        if (args.variants > 1):
            variant_id = string.ascii_uppercase[i]

        variant = quiz.create_variant(identifier = variant_id)
        out_path = os.path.join(out_dir, "%s.json" % (variant.title))
        quizgen.util.file.write(out_path, variant.to_json(include_docs = False))

        if (args.upload):
            converter = quizgen.converter.gradescope.GradeScopeUploader(args.course_id, args.user, args.password,
                    force = args.force, rubric = args.rubric)
            gradescope_id = converter.convert_quiz(variant, base_dir = out_dir)
            gradescope_ids.append(gradescope_id)
        else:
            _make_pdf(variant, out_dir, False)

        title = variant.title

        # Always create an answer key.
        try:
            variant.title = "%s -- Answer Key" % (variant.title)
            _make_pdf(variant, out_dir, True)
        except Exception as ex:
            print("WARN: Failed to generate answer key for '%s'." % (title))

        print("Completed variant: '%s'." % (title))

    if (len(gradescope_ids) > 1):
        converter = quizgen.converter.gradescope.GradeScopeUploader(args.course_id, args.user, args.password)
        converter.create_assignment_group(quiz.title, gradescope_ids)
        print("Created GradeScope Assignment Group: '%s'." % (quiz.title))

    return 0

def _make_pdf(variant, out_dir, is_key):
    converter = quizgen.converter.gstemplate.GradeScopeTemplateConverter(answer_key = is_key)
    content = converter.convert_quiz(variant)

    out_path = os.path.join(out_dir, "%s.tex" % (variant.title))
    quizgen.util.file.write(out_path, content)

    # Need to compile twice to get positioning.
    quizgen.latex.compile(out_path)
    quizgen.latex.compile(out_path)

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a quiz and upload the quiz to Canvas.")

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

    return parser

def main():
    return run(_get_parser().parse_args())

if (__name__ == '__main__'):
    sys.exit(main())
