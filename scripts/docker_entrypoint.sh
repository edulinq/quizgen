#!/bin/bash

pdflatex -interaction=nonstopmode "$1"
pdflatex -interaction=nonstopmode "$1"

INPUT_OWNER=$(stat -c "%u:%g" "$1")
chown "$INPUT_OWNER" "${1%.tex}.pdf" "${1%.tex}.aux" "${1%.tex}.log" "${1%.tex}.out" "${1%.tex}.pos" 2>/dev/null || true