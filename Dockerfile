FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y
RUN apt-get install openssh-client sshpass rsync -y

COPY . /code
WORKDIR /code
RUN python setup.py install
