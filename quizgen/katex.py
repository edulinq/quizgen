import shutil
import subprocess
import sys

ENCODING = 'utf-8'

def _has_command(command, cwd = '.'):
    result = subprocess.run(["which", command], cwd = cwd, capture_output = True)
    return (result.returncode == 0)

def _has_package(package, cwd = '.'):
    result = subprocess.run(["npm", "list", package], cwd = cwd, capture_output = True)
    return (result.returncode == 0)

def is_available(cwd = '.'):
    if (shutil.which('npx') is None):
        print("WARN: Could not find `npx` (usually installed with `npm`), cannot use katex equations.", file = sys.stderr)
        return False

    if (not _has_package('katex', cwd = cwd)):
        print("WARN: Could not find the `katex` package, cannot use katex equations.", file = sys.stderr)
        return False

    return True

def to_html(text, cwd = '.'):
    result = subprocess.run(["npx", "katex", "--format", "mathml"], cwd = cwd,
        input = text, encoding = ENCODING,
        capture_output = True)

    if (result.returncode != 0):
        raise ValueError("KaTeX did not exit cleanly. Stdout: '%s', Stderr: '%s'" % (result.stdout, result.stderr))

    return result.stdout
