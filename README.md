[![Build Status](https://travis-ci.org/fhirbase/fhirbase.py.svg?branch=master)](https://travis-ci.org/fhirbase/fhirbase.py)
[![pypi](https://img.shields.io/pypi/v/fhirbase.svg)](https://pypi.python.org/pypi/fhirbase)

# fhirbase.py
FHIRBase connector for python.
This package provides CRUD on resourses in fhirbase.


# Example
To run example, just do:

```
docker-compose build
docker-compose up -d
docker-compose run --rm db fhirbase -d postgres init 3.0.1
docker-compose run --rm fhirbase python examples/example.py
```
