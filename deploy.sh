#!/bin/bash

# Deploy to PyPi Test and PyPi.
# Assume pypi credentials exist in one of the standard locations.

readonly THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function main() {
    if [[ $# -ne 0 ]]; then
        echo "USAGE: $0"
        exit 1
    fi

    set -e
    trap exit SIGINT

    cd "${THIS_DIR}"

    rm -rf "dist"

    python3 -m build
    python3 -m twine upload -r testpypi dist/*
    python3 -m twine upload dist/*
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
