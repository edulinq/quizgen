#!/bin/bash

# Check if Docker is installed or not
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker to use this script."
    exit 1
fi

# Set default input file
INPUT_FILE=${1:-"quiz.tex"}

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found."
    exit 1
fi

# Run pdflatex inside Docker
docker run --rm -v "$(pwd)":/workspace quizgen-tex pdflatex -interaction=nonstopmode "$INPUT_FILE"

# Check if the PDF was generated
if [ -f "${INPUT_FILE%.tex}.pdf" ]; then
    echo "PDF generated successfully: ${INPUT_FILE%.tex}.pdf"
else
    echo "Error: PDF generation failed. Check the logs above."
    exit 1
fi