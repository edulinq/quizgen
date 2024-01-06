import os
import shutil
import subprocess
import sys

def is_available():
    if (shutil.which('pdflatex') is None):
        print("WARN: Could not find `pdxlatex`, cannot compile PDFs", file = sys.stderr)
        return False

    return True

def compile(path):
    result = subprocess.run(["pdflatex", path], cwd = os.path.dirname(path),
        capture_output = True)

    if (result.returncode != 0):
        raise ValueError("pdflatex did not exit cleanly. Stdout: '%s', Stderr: '%s'" % (result.stdout, result.stderr))
