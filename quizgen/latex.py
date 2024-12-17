import logging
import os
import shutil
import subprocess

_pdflatex_bin_path = None

def set_pdflatex_bin_path(path):
    global _pdflatex_bin_path
    _pdflatex_bin_path = path

def is_available():
    if (_pdflatex_bin_path is not None):
        return True

    if (shutil.which('pdflatex') is None):
        logging.warning("Could not find `pdxlatex`, cannot compile PDFs")
        return False

    return True

def compile(path):
    bin_path = 'pdflatex'
    if (_pdflatex_bin_path is not None):
        bin_path = _pdflatex_bin_path

    result = subprocess.run([bin_path, '-interaction=nonstopmode', os.path.basename(path)], cwd = os.path.dirname(path),
        capture_output = True)

    if (result.returncode != 0):
        raise ValueError("pdflatex did not exit cleanly. Stdout: '%s', Stderr: '%s'" % (result.stdout, result.stderr))

def set_cli_args(parser):
    parser.add_argument('--pdflatex-bin-path', dest = 'pdflatex_bin_path',
        action = 'store', type = str, default = None,
        help = ('The path to the pdflatex binary to use.'
                + ' If not specified, $PATH will be searched.'
                + ' Used to compile PDFs.'))

    return parser

def init_from_args(args):
    if (args.pdflatex_bin_path is not None):
        set_pdflatex_bin_path(args.pdflatex_bin_path)

    return args
