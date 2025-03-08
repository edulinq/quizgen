#!/bin/bash
cd "$(dirname "$1")" || exit 1

# Double compilation to get correct references

pdflatex -interaction=nonstopmode "$(basename "$1")"
pdflatex -interaction=nonstopmode "$(basename "$1")"

# Change owner of output files to the owner of the input file

INPUT_OWNER=$(stat -c "%u:%g" "$1")
chown "$INPUT_OWNER" "${1%.tex}.pdf" "${1%.tex}.aux" "${1%.tex}.log" "${1%.tex}.out" "${1%.tex}.pos" 2>/dev/null || true