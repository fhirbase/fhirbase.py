[![Build Status](https://travis-ci.org/fhirbase/fhirbase.py.svg?branch=master)](https://travis-ci.org/fhirbase/fhirbase.py)
[![pypi](https://img.shields.io/pypi/v/fhirbase.svg)](https://pypi.python.org/pypi/fhirbase)

# fhirbase.py
FHIRBase connector for python.
This package provides CRUD on resourses in fhirbase.

# Install
```
pip install fhirbase
```

# Example
To run example, just do:

```
docker-compose build
docker-compose up -d
```
Wait until db starting process will be completed, and run:

```
docker-compose run --rm fhirbase fhirbase init 3.0.1
docker-compose run --rm fhirbasepy python examples/example.py
```
