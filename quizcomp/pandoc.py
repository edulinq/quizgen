# TEST
import logging
import os
import shutil
import subprocess

import quizcomp.util.dirent

_pandoc_bin_path = None
_pandoc_use_docker = False

DOCKER_IMAGE = "pandoc/core:3.7.0.2"

def set_pandoc_bin_path(path):
    global _pandoc_bin_path
    _pandoc_bin_path = path

def set_pandoc_use_docker(pandoc_use_docker):
    global _pandoc_use_docker
    _pandoc_use_docker = pandoc_use_docker

def is_available():
    if (_pandoc_use_docker):
        if (not _is_docker_available()):
            logging.warning("Docker is not available, cannot use pandoc.")
            return False

        return True

    if (_pandoc_bin_path is not None):
        return True

    if (shutil.which('pandoc') is None):
        logging.warning("Could not find `pandoc`.")
        return False

    return True

def _is_docker_available():
    if (shutil.which('docker') is None):
        return False

    result = subprocess.run(["docker", "info"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    return (result.returncode == 0)

def convert_string(in_text, in_format, out_format):
    """
    Use pandoc to convert text from one format to another.
    Formats must be provided.
    """

    temp_dir = quizcomp.util.dirent.get_temp_path(prefix = 'quizcomp-pandoc-string-')
    in_path = os.path.join(temp_dir, 'in')
    out_path = os.path.join(temp_dir, 'out')

    quizcomp.util.dirent.write_file(in_path, in_text)

    convert_file(in_path, out_path, in_format = in_format, out_format = out_format)

    return quizcomp.util.dirent.read_file(out_path)

def convert_file(in_path, out_path, in_format = None, out_format = None):
    """
    Use pandoc to convert an existing file.
    If formats are not provided, pandoc will guess.
    """

    if (_pandoc_use_docker is True):
        _convert_file_docker(in_path, out_path, in_format = in_format, out_format = out_format)
    else:
        _convert_file_local(in_path, out_path, in_format = in_format, out_format = out_format)

def _convert_file_local(in_path, out_path, in_format = None, out_format = None):
    bin_path = "pandoc"
    if (_pandoc_bin_path is not None):
        bin_path = _pandoc_bin_path

    args = [bin_path]
    args += _build_base_args(in_path, out_path, in_format = in_format, out_format = out_format)

    result = subprocess.run(args, capture_output = True)
    if (result.returncode != 0):
        raise ValueError("Local pandoc failed with exit code '%s'. Stdout: '%s', Stderr: '%s'" % (result.returncode, result.stdout, result.stderr))

def _convert_file_docker(in_path, out_path, in_format = None, out_format = None):
    temp_dir = quizcomp.util.dirent.get_temp_path(prefix = 'quizcomp-pandoc-docker-')

    in_ext = os.path.splitext(in_path)[-1]
    temp_in_filename = f"in{in_ext}"
    temp_in_path = os.path.join(temp_dir, temp_in_filename)

    out_ext = os.path.splitext(out_path)[-1]
    temp_out_filename = f"out{out_ext}"
    temp_out_path = os.path.join(temp_dir, temp_out_filename)

    quizcomp.util.dirent.copy_dirent(in_path, temp_in_path)

    # TEST - Check permissions
    args = [
        "docker", "run", "--rm",
        "-v", f"{temp_dir}:/data",
        DOCKER_IMAGE,
    ]
    args += _build_base_args(temp_in_filename, temp_out_filename, in_format = in_format, out_format = out_format)

    result = subprocess.run(args, capture_output = True, text = True)
    if (result.returncode != 0):
        raise ValueError("Docker pandoc failed with exit code '%s'. Stdout: '%s', Stderr: '%s'" % (result.returncode, result.stdout, result.stderr))

def _build_base_args(in_path, out_path, in_format = None, out_format = None):
    args = [
        in_path,
        '--output', out_path,
    ]

    if (in_format is not None):
        args += ['--from', in_format]

    if (out_format is not None):
        args += ['--to', out_format]

    return args

def set_cli_args(parser):
    parser.add_argument('--pandoc-bin-path', dest = 'pandoc_bin_path',
        action = 'store', type = str, default = None,
        help = ('The path to the pandoc binary to use.'
                + ' If not specified, $PATH will be searched.'
                + ' Used to convert non-native quizzes to the Quiz Composer format.'))

    parser.add_argument('--pandoc-use-docker', dest = 'pandoc_use_docker',
        action = 'store_true', default = False,
        help = ('Use Docker to invoke pandoc.'
                + " The Docker image '%s' will be used." % (DOCKER_IMAGE)))

    return parser

def init_from_args(args):
    if (args.pandoc_use_docker):
        set_pandoc_use_docker(args.pandoc_use_docker)

    if (args.pandoc_bin_path is not None):
        set_pandoc_bin_path(args.pandoc_bin_path)

    return args
