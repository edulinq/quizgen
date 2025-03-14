import logging
import os
import shutil
import subprocess

import quizgen.util.dirent

_pdflatex_bin_path = None
_pdflatex_use_docker = False

DOCKER_IMAGE = "quizgen/latex.py"

def set_pdflatex_bin_path(path):
    global _pdflatex_bin_path
    _pdflatex_bin_path = path

def set_pdflatex_use_docker(pdflatex_use_docker):
    global _pdflatex_use_docker
    _pdflatex_use_docker = pdflatex_use_docker

def is_available():
    if (_pdflatex_use_docker):
        result = subprocess.run(["docker", "info"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

        if (result.returncode != 0):
            logging.warning("Docker is not available, cannot compile PDFs")
            return False

        return True

    if (_pdflatex_bin_path is not None):
        return True

    if (shutil.which('pdflatex') is None):
        logging.warning("Could not find `pdxlatex`, cannot compile PDFs")
        return False

    return True

def compile(path, additional_paths = []):

    if (_pdflatex_use_docker):
        _compile_docker(path, additional_paths = additional_paths)
    else:
        # Need to compile twice to get positioning information.
        _compile_local(path)
        _compile_local(path)

def _compile_local(path):
    bin_path = "pdflatex"
    if (_pdflatex_bin_path is not None):
        bin_path = _pdflatex_bin_path

    result = subprocess.run([bin_path, '-interaction=nonstopmode', os.path.basename(path)], cwd = os.path.dirname(path),
        capture_output = True)

    if (result.returncode != 0):
        raise ValueError("pdflatex did not exit cleanly. Stdout: '%s', Stderr: '%s'" % (result.stdout, result.stderr))

def _compile_docker(path, additional_paths = []):
    """
    Compile a LaTeX file using Docker.

    Args:
        path: Path to the LaTeX file to compile.
        additional_paths: List of additional directory paths that should be 
                          accessible during compilation. These will be placed at the
                          same relative location to the tex file as in the original
                          directory structure.
        out_dir: Directory to place compilation output files.
    """

    temp_dir = quizgen.util.dirent.get_temp_path(prefix = 'quizgen_latex_')
    temp_tex = os.path.join(temp_dir, os.path.basename(path))

    quizgen.util.dirent.copy_dirent(path, temp_tex)

    # Copy any additional required paths.
    for add_path in additional_paths:
        if (os.path.exists(add_path)):
            rel_path = os.path.basename(add_path)
            dest_path = os.path.join(temp_dir, rel_path)

            if (os.path.isdir(add_path)):
                shutil.copytree(add_path, dest_path, dirs_exist_ok = True)
            else:
                os.makedirs(os.path.dirname(dest_path), exist_ok = True)
                shutil.copy(add_path, dest_path)

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{temp_dir}:/work",
        DOCKER_IMAGE,
        os.path.basename(temp_tex)
    ]

    result = subprocess.run(docker_cmd, capture_output = True, text = True)

    if (result.returncode != 0):
        raise ValueError(f"Docker compilation failed with exit code {result.returncode}. Stdout: '{result.stdout}', Stderr: '{result.stderr}'")

    base_name = os.path.basename(temp_tex)
    target_dir = os.path.dirname(path)

    for ext in [".pdf", ".aux", ".log", ".out", ".pos"]:
        temp_file = os.path.join(temp_dir, base_name.replace(".tex", ext))
        if os.path.exists(temp_file):
            shutil.copy(temp_file, os.path.join(target_dir, os.path.basename(temp_file)))
        else:
            logging.error(f"Expected file {temp_file} not generated")



def set_cli_args(parser):
    parser.add_argument('--pdflatex-bin-path', dest = 'pdflatex_bin_path',
        action = 'store', type = str, default = None,
        help = ('The path to the pdflatex binary to use.'
                + ' If not specified, $PATH will be searched.'
                + ' Used to compile PDFs.'))

    parser.add_argument('--pdflatex-use-docker', dest = 'pdflatex_use_docker',
        action = 'store_true', default = False,
        help = ('Use Docker to compile PDFs with pdflatex.'
                + f' The Docker image `{DOCKER_IMAGE}` will be used.'))

    return parser

def init_from_args(args):
    if (args.pdflatex_use_docker):
        set_pdflatex_use_docker(args.pdflatex_use_docker)

    if (args.pdflatex_bin_path is not None):
        set_pdflatex_bin_path(args.pdflatex_bin_path)

    return args