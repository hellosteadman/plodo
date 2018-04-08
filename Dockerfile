FROM python:3.6
ENV PYTHONUNBUFFERED 1

COPY . /code
WORKDIR /code
RUN python setup.py install
