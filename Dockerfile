FROM ubuntu:20.04

LABEL maintainer="gururaj.krishnamurthy@gmail.com"
LABEL version="0.1"
LABEL description="This is Docker Image for websensor project"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install --no-install-recommends -y \
    vim curl \
    cmake \
    tesseract-ocr \
    ca-certificates \
    python3.8 python3.8-distutils \
    python3-opencv python3-dev libffi-dev libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.8 get-pip.py

RUN apt update && apt install --install-recommends -y gcc && rm -rf /var/lib/apt/lists/*

COPY websensor requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

# VOLUME ["/config/websensor.secrets"]

ENV WEBSENSORRC /config/websensor.rc
COPY websensor.rc /config/
RUN mkdir /tmp/websensor

ENTRYPOINT ["python3.8", "/app/cli.py"]
CMD ["--help"]
