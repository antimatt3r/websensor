FROM ubuntu:20.04

LABEL maintainer="gururaj.krishnamurthy@gmail.com"
LABEL version="0.1"
LABEL description="This is Docker Image for websensor project"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y \
    vim \
    curl

RUN apt install -y python3 python3-pip

COPY websensor requirements.txt /app/
WORKDIR /app
RUN pip3 install -r requirements.txt

RUN apt install -y tesseract-ocr

# VOLUME ["/config/websensor.rc", "/config/websensor.secrets"]

ENV WEBSENSORRC /config/websensor.rc
RUN mkdir /tmp/websensor

ENTRYPOINT ["python3", "/app/cli.py"]
CMD ["--help"]
