!/bin/bash

Compiling twice to resolve references
pdflatex -interaction=nonstopmode "$1"
pdflatex -interaction=nonstopmode "$1"

Change owner of output files to match input file
INPUT_OWNER=$(stat -c "%u:%g" "$1")
chown "$INPUT_OWNER" "${1%.tex}.pdf" "${1%.tex}.aux" "${1%.tex}.log" 2>/dev/null || true