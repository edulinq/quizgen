# Use a lightweight TeX base image
FROM texlive/texlive:latest

# Set working directory
WORKDIR /workspace

# Install any additional tools if needed (optional)
RUN tlmgr update --self && \
    tlmgr install latexmk


CMD ["pdflatex", "--version"]