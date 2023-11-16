import os
import subprocess
import sys

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
ROOT_DIR = os.path.join(THIS_DIR, '..')

ENCODING = 'utf-8'

def _has_command(command, cwd = ROOT_DIR):
    result = subprocess.run(["which", command], cwd = cwd, capture_output = True)
    return (result.returncode == 0)

def _has_package(package, cwd = ROOT_DIR):
    result = subprocess.run(["npm", "list", package], cwd = cwd, capture_output = True)
    return (result.returncode == 0)

def is_available(cwd = ROOT_DIR):
    if (not _has_command('npx', cwd = cwd)):
        print("WARN: Could not find `npx` (usually installed with `npm`), cannot use katex equations.", file = sys.stderr)
        return False

    if (not _has_package('katex', cwd = cwd)):
        print("WARN: Could not find the `katex` package, cannot use katex equations.", file = sys.stderr)
        return False

    return True

def to_html(text, cwd = ROOT_DIR):
    result = subprocess.run(["npx", "katex", "--format", "mathml"], cwd = cwd,
        input = text, encoding = ENCODING,
        capture_output = True, check = True)

    return result.stdout
