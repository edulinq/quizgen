import logging
import os
import shutil
import subprocess

def is_available():
    if (shutil.which('pdflatex') is None):
        logging.warning("Could not find `pdxlatex`, cannot compile PDFs")
        return False

    return True

def compile(path):
    result = subprocess.run(['pdflatex', '-interaction=nonstopmode', os.path.basename(path)], cwd = os.path.dirname(path),
        capture_output = True)

    if (result.returncode != 0):
        raise ValueError("pdflatex did not exit cleanly. Stdout: '%s', Stderr: '%s'" % (result.stdout, result.stderr))
