import datetime
import json
import logging
import os
import random
import string
import traceback

import quizgen.converter.textemplate
import quizgen.latex
import quizgen.util.file
import quizgen.quiz

OPTIONS_FILENAME = 'options.json'

def make_with_args(args, **kwargs):
    """
    Use a standard args object from set_cli_args() to make a PDF quiz.
    """

    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    if ((args.variants < 1) or (args.variants >= len(string.ascii_uppercase))):
        raise ValueError("Number of variants must be in [1, %d), found %d." % (len(string.ascii_uppercase), args.variants))

    return make(args.path, args.out_dir, seed = args.seed, num_variants = args.variants,
            skip_key = args.skip_key, skip_tex = args.skip_tex, skip_pdf = args.skip_pdf,
            **kwargs)

def make(quiz_path, base_out_dir,
        seed = None, num_variants = 1, write_options = True,
        skip_key = False, skip_tex = False, skip_pdf = False,
        **kwargs):
    quiz = quizgen.quiz.Quiz.from_path(quiz_path)

    out_dir = os.path.join(base_out_dir, quiz.title)
    os.makedirs(out_dir, exist_ok = True)

    logging.info("Writing TeX/PDF quiz ('%s') to '%s'.", quiz.title, out_dir)

    if (seed is None):
        seed = random.randint(0, 2**64)

    options = {
        'create_time': datetime.datetime.now().isoformat(),
        'seed': seed,
        'out_dir': out_dir,
        'quiz': {
            'path': quiz_path,
            'title': quiz.title,
            'version': quiz.version,
        },
        'variants': [],
    }

    logging.info("Using seed %d.", seed)
    rng = random.Random(seed)

    variants = []
    for i in range(num_variants):
        variant_id = None
        if (num_variants > 1):
            variant_id = string.ascii_uppercase[i]

        variant_seed = rng.randint(0, 2**64)
        variant = quiz.create_variant(identifier = variant_id, seed = variant_seed)
        variants.append(variant)

        out_path = os.path.join(out_dir, "%s.json" % (variant.title))
        quizgen.util.file.write(out_path, variant.to_json(include_docs = False))

        make_pdf(variant, out_dir, False, skip_tex = skip_tex, skip_pdf = skip_pdf)

        title = variant.title

        # Always create an answer key.
        has_key = False
        if (not skip_key):
            try:
                variant.title = "%s -- Answer Key" % (title)
                make_pdf(variant, out_dir, True, skip_tex = skip_tex, skip_pdf = skip_pdf)
                has_key = True
            except Exception as ex:
                logging.warning("Failed to generate answer key for '%s'.", title)
                logging.debug(traceback.format_exc())
            finally:
                variant.title = title

        options['variants'].append({
            'id': variant_id,
            'title': title,
            'seed': variant_seed,
            'has_key': has_key,
        })

        logging.info("Completed variant: '%s'.", title)

    if (write_options):
        path = os.path.join(out_dir, OPTIONS_FILENAME)
        with open(path, 'w') as file:
            json.dump(options, file, indent = 4)

    return (quiz, variants, options)

def make_pdf(variant, out_dir, is_key,
        skip_tex = False, skip_pdf = False):
    image_relative_root = os.path.join('images', variant.title)
    image_dir = os.path.join(out_dir, image_relative_root)

    out_path = os.path.join(out_dir, "%s.tex" % (variant.title))

    if (not skip_tex):
        converter = quizgen.converter.textemplate.TexTemplateConverter(answer_key = is_key,
                image_base_dir = image_dir, image_relative_root = image_relative_root, cleanup_images = True)
        content = converter.convert_variant(variant)

        quizgen.util.file.write(out_path, content)

    if (not skip_pdf):
        # Need to compile twice to get positioning.
        quizgen.latex.compile(out_path)
        quizgen.latex.compile(out_path)

def set_cli_args(parser):
    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz json file.')

    parser.add_argument('--variants', dest = 'variants',
        action = 'store', type = int, default = 1,
        help = 'The number of quiz variants to create (default: %(default)s).')

    parser.add_argument('--outdir', dest = 'out_dir',
        action = 'store', type = str, default = '.',
        help = 'The directory to put the quiz creation output (which will be another directory) (default: %(default)s).')

    parser.add_argument('--skip-key', dest = 'skip_key',
        action = 'store_true', default = False,
        help = 'Skip creating the answer key (default: %(default)s).')

    parser.add_argument('--skip-tex', dest = 'skip_tex',
        action = 'store_true', default = False,
        help = 'Skip creating TeX files (assumes the TeX files already exist) (default: %(default)s).')

    parser.add_argument('--skip-pdf', dest = 'skip_pdf',
        action = 'store_true', default = False,
        help = 'Skip compiling PDFs from TeX (assumes the PDFs already exist) (default: %(default)s).')

    parser.add_argument('--seed', dest = 'seed',
        action = 'store', type = int, default = None,
        help = 'The random seed to use (defaults to a random seed).')

    return parser
