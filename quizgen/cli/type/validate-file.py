import argparse
import sys

import quizgen.log
import quizgen.jtype.validator
import quizgen.util.file

def run(args):
    content = quizgen.util.file.read(args.content_path)
    definition = quizgen.util.file.read(args.definition_path)

    is_valid = quizgen.jtype.validator.validate(definition, content,
            raise_on_error = args.raise_on_error, log_on_error = args.log_on_error,
            ignore_extra_fields = args.ignore_extra_fields,
            base_dir = args.base_dir)

    if (not args.quiet):
        if (is_valid):
            print("Valid")
        else:
            print("Invalid")

    return int(is_valid)

def _get_parser():
    parser = argparse.ArgumentParser(description =
        "Validate a JSON file against a JSON JType definition.")

    parser.add_argument('content_path', metavar = 'CONTENT_PATH',
        type = str,
        help = 'The path to the content to validate.')

    parser.add_argument('definition_path', metavar = 'DEFINITION_PATH',
        type = str,
        help = 'The path to the JType definition to validate against.')

    parser.add_argument('--raise', dest = 'raise_on_error',
        action = 'store_true', default = False,
        help = 'Raise a Python exception on validation error (default: %(default)s).')

    parser.add_argument('--log', dest = 'log_on_error',
        action = 'store_true', default = False,
        help = 'Log when a validation error occurs (default: %(default)s).')

    parser.add_argument('--ignore-extra', dest = 'ignore_extra_fields',
        action = 'store_true', default = False,
        help = 'Ignore extra fields in the content that are not present in the type definition (default: %(default)s).')

    parser.add_argument('--base-dir', dest = 'base_dir',
        action = 'store', type = str, default = None,
        help = 'Where relative paths are relative from. If not specified, relative paths will not be verified.')

    parser.add_argument('--quiet', dest = 'quiet',
        action = 'store_true', default = False,
        help = 'Do not output additional text about the result of validation (default: %(default)s).')

    quizgen.log.set_cli_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    quizgen.log.init_from_args(args)
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
