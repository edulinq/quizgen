import logging
import os
import shutil
import subprocess

import quizgen.util.dirent

_pdflatex_bin_path = None
_pdflatex_use_docker = False

DOCKER_IMAGE = "edulinq/quizgen-tex:latest"

def set_pdflatex_bin_path(path):
    global _pdflatex_bin_path
    _pdflatex_bin_path = path

def set_pdflatex_use_docker(use_docker):
    global _pdflatex_use_docker
    _pdflatex_use_docker = use_docker

def is_available(use_docker = False):
    if use_docker:
        result = subprocess.call(["docker", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result != 0:
            logging.warning("Docker is not installed, cannot compile PDFs with --use-docker.")
            return False
        return True
    
    if (_pdflatex_bin_path is not None):
        return True

    if (shutil.which('pdflatex') is None):
        logging.warning("Could not find `pdxlatex`, cannot compile PDFs")
        return False

    return True

def compile(path):
    if _pdflatex_use_docker:
        return _compile_docker(path)
    return _compile_local(path)

def _compile_local(path):
    bin_path = _pdflatex_bin_path or "pdflatex"
    result = subprocess.run(
        [bin_path, "-interaction=nonstopmode", os.path.basename(path)],
        cwd=os.path.dirname(path),
        capture_output=True
    )
    return result.returncode == 0

def _compile_docker(path):
    temp_dir = quizgen.util.dirent.get_temp_path()
    temp_tex = os.path.join(temp_dir, os.path.basename(path))
    quizgen.util.dirent.copy_dirent(path, temp_tex)

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{temp_dir}:/work",
            DOCKER_IMAGE,
            os.path.basename(temp_tex)
        ],
        capture_output=True
    )
    
    if result.returncode == 0:
        shutil.copy(temp_tex.replace(".tex", ".pdf"), os.path.dirname(path))

    quizgen.util.dirent.remove_dirent(temp_dir)
    return result.returncode == 0

def set_cli_args(parser):
    parser.add_argument('--pdflatex-bin-path', dest='pdflatex_bin_path',
        action='store', type=str, default=None,
        help=('The path to the pdflatex binary to use. '
              + 'If not specified, $PATH will be searched. '
              + 'Used to compile PDFs when not using Docker.'))
    
    parser.add_argument('--use-docker',dest='use_docker',
        action='store_true', default = False,
        help='Use Docker to compile PDFs instead of local pdflatex (default: %(default)s).')

    return parser

def init_from_args(args):
    
    if (args.use_docker):
        set_pdflatex_use_docker(True)
        return args
        
    if (args.pdflatex_bin_path is not None):
        set_pdflatex_bin_path(args.pdflatex_bin_path)

    return args
