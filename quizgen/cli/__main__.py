"""
The `quizgen.cli` package contains tools for running the quizgen.
Each package can be invoked to list the tools (or subpackages) it contains.
Each tool includes a help prompt that accessed with the `-h`/`--help` flag.
"""

import sys

import quizgen.util.cli

def main():
    return quizgen.util.cli.main()

if (__name__ == '__main__'):
    sys.exit(main())
