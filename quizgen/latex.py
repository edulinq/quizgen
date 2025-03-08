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
        result = subprocess.call(["docker", "--version"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        return result == 0
    return _pdflatex_bin_path is not None or shutil.which('pdflatex') is not None

def compile(path):
    if _pdflatex_use_docker:
        return _compile_docker(path)
    return _compile_local(path)

def _compile_local(path):
    bin_path = _pdflatex_bin_path or "pdflatex"
    result = subprocess.run(
        [bin_path, "-interaction=nonstopmode", os.path.basename(path)],
        cwd=os.path.dirname(path),
        capture_output = True
    )
    return result.returncode == 0

def _compile_docker(path):
    temp_dir = quizgen.util.dirent.get_temp_path()
    temp_tex = os.path.join(temp_dir, os.path.basename(path))
    
    quizgen.util.dirent.copy_dirent(path, temp_tex)
    
    source_dir = os.path.dirname(path)
    images_dir = os.path.join(source_dir, 'images')
    if os.path.exists(images_dir):
        dest_images_dir = os.path.join(temp_dir, 'images')
        shutil.copytree(images_dir, dest_images_dir, dirs_exist_ok=True)

    logging.info(f"Compiling {temp_tex} with Docker")
    
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{temp_dir}:/work",
        DOCKER_IMAGE,
        os.path.basename(temp_tex)
    ]

    result = subprocess.run(docker_cmd, capture_output = True, text = True)

    if result.returncode != 0:
        logging.error(f"Docker compilation failed with exit code {result.returncode}")

    if result.returncode == 0:
        base_name = os.path.basename(temp_tex)
        target_dir = os.path.dirname(path)
        for ext in [".pdf", ".aux", ".log", ".out", ".pos"]:
            temp_file = os.path.join(temp_dir, base_name.replace(".tex", ext))
            if os.path.exists(temp_file):
                shutil.copy(temp_file, os.path.join(target_dir, os.path.basename(temp_file)))
            else:
                logging.warning(f"Expected file {temp_file} not generated")
    else:
        logging.error(f"Compilation failed, no files copied back")

    quizgen.util.dirent.remove_dirent(temp_dir)
    return result.returncode == 0

def set_cli_args(parser):
    parser.add_argument('--pdflatex-bin-path', dest = 'pdflatex_bin_path',
        action = 'store', type = str, default = None,
        help = 'Path to pdflatex binary (used without Docker).')
    parser.add_argument('--use-docker', dest = 'use_docker',
        action = 'store_true', default = False,
        help = 'Use Docker to compile PDFs.')
    return parser

def init_from_args(args):
    if args.use_docker:
        set_pdflatex_use_docker(True)
    if args.pdflatex_bin_path:
        set_pdflatex_bin_path(args.pdflatex_bin_path)
    return args