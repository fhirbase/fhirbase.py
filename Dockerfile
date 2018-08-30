FROM python:3.6-slim

RUN mkdir -p /app/user
RUN mkdir /src
WORKDIR /app/user
ADD . /app/user

RUN python setup.py sdist
RUN pip install --src /src -r requirements.txt
RUN pip install --src /src dist/fhirbase-*.tar.gz
