#!/bin/bash

# Docker entrypoint script to compile a TeX file into a PDF using pdflatex.
# The script compiles the input file twice to ensure correct references and
# adjusts the ownership of output files to match the input file's owner and group.

readonly THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="${THIS_DIR}/.."

function main() {
      set -e
      trap exit SIGINT

      local tex_path="$1"

      if [ -z "${tex_path}" ]; then
            echo "Error: No TeX file path provided." >&2
            exit 2
      fi

      if [ ! -f "${tex_path}" ]; then
            echo "Error: TeX file '${tex_path}' does not exist." >&2
            exit 3
      fi

      local base_name=$(basename "${tex_path}")

      # Double compilation to get correct references.
      pdflatex -interaction=nonstopmode "${base_name}"
      pdflatex -interaction=nonstopmode "${base_name}"

      # Change owner of output files to match the input file.
      local owner_group=$(stat -c "%u:%g" "${tex_path}")
      chown -R "${owner_group}" /work
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"