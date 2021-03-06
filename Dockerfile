FROM ubuntu:18.04

LABEL maintainer="gururaj.krishnamurthy@gmail.com"
LABEL version="0.1"
LABEL description="This is Docker Image for websensor project"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install --no-install-recommends -y \
    vim curl \
    cmake \
    tesseract-ocr \
    ca-certificates \
    python3.8 python3.8-distutils \
    python3-opencv python3.8-dev libffi-dev libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.8 get-pip.py

RUN apt update \
    && apt install --install-recommends -y \
        gcc libpython3-dev build-essential libpython3-dev python3-setuptools python3-pil \
        liblcms2-2 libwebpdemux2 libwebp6 libtiff5 libwebpmux3 libjbig0 libopenjp2-7 \
    && rm -rf /var/lib/apt/lists/*

COPY websensor requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

# VOLUME ["/config/websensor.secrets"]

ENV WEBSENSORRC /config/websensor.rc
COPY websensor.rc /config/
RUN mkdir /tmp/websensor

ENV PYTHONIOENCODING UTF-8

# ENTRYPOINT ["python3.8", "/app/cli.py"]
# CMD ["--help"]

WORKDIR /app

EXPOSE 8080
CMD ["gunicorn", "-c", "/app/gunicorn_config.py", "wsgi:app"]
