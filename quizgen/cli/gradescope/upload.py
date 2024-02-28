"""
Upload a gradescope quiz that has already been created via create-gradescope-quiz.
"""

import argparse
import logging
import os
import string
import sys

import quizgen.converter.textemplate
import quizgen.latex
import quizgen.log
import quizgen.uploader.gradescope
import quizgen.util.file
import quizgen.variant

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    variant_path = os.path.abspath(args.path)
    base_dir = os.path.dirname(variant_path)

    variant = quizgen.variant.Variant.from_path(variant_path)

    logging.info("Writing generated output to '%s'.", base_dir)

    uploader = quizgen.uploader.gradescope.GradeScopeUploader(args.course_id, args.user, args.password,
            force = args.force, rubric = args.rubric,
            skip_tex_write = args.skip_tex_write, skip_compile = args.skip_compile)
    gradescope_id = uploader.upload_quiz(variant, base_dir = base_dir)

    title = variant.title

    try:
        variant.title = "%s -- Answer Key" % (variant.title)
        _make_pdf(variant, base_dir, True, args.skip_tex_write, args.skip_compile)
    except Exception as ex:
        logging.warning("Failed to generate answer key for '%s'.", title)

    logging.info("Completed variant: '%s'.", title)

    return 0

def _make_pdf(variant, base_dir, is_key, skip_tex_write, skip_compile):
    image_relative_root = os.path.join('images', variant.title)
    image_dir = os.path.join(base_dir, image_relative_root)

    converter = quizgen.converter.textemplate.TexTemplateConverter(answer_key = is_key,
            image_base_dir = image_dir, image_relative_root = image_relative_root, cleanup_images = True)
    content = converter.convert_variant(variant)

    out_path = os.path.join(base_dir, "%s.tex" % (variant.title))

    if (not skip_tex_write):
        quizgen.util.file.write(out_path, content)

    if (not skip_compile):
        # Need to compile twice to get positioning.
        quizgen.latex.compile(out_path)
        quizgen.latex.compile(out_path)

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Parse a single variant output generated by create-gradescope-quiz and upload the quiz to GradeScope."
        + " Most users should be using create-gradescope-quiz instead.")

    parser.add_argument('path',
        type = str,
        help = 'The path to a variant JSON file. It will be assumed that all the necessary supporting files are adjacent to this.')

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

    parser.add_argument('--skip-tex', dest = 'skip_tex_write',
        action = 'store_true', default = False,
        help = 'Skip creating the tex file for this variant (assumes the tex file already exists).')

    parser.add_argument('--skip-compile', dest = 'skip_compile',
        action = 'store_true', default = False,
        help = 'Skip compiling the tex file for this variant (assumes the pdf is already compiled).')

    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
