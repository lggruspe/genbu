ARG PYTHON_IMAGE=python:3.9-alpine
FROM $PYTHON_IMAGE
RUN apk add gcc libc-dev make
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY . /genbu
WORKDIR /genbu
CMD make test && make lint
