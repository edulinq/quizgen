FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y texlive && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
CMD ["pdflatex", "--version"]