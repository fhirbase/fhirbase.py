[![Build Status](https://travis-ci.org/fhirbase/fhirbase.py.svg?branch=master)](https://travis-ci.org/fhirbase/fhirbase.py)
[![pypi](https://img.shields.io/pypi/v/fhirbase.svg)](https://pypi.python.org/pypi/fhirbase)

# fhirbase.py
FHIRBase connector for python.
This package provides wrapper over psycopg2 connection which
provides CRUD for resources in fhirbase.

# Install
```
pip install fhirbase
```

# Usage
Import `fhirbase` and `psycopg2` libraries:
```
import fhirbase
import psycopg2
```

Create a connection using `psycopg2.connect`;

```
connection = psycopg2.connect(
    dbname='postgres', user='postgres',
    host='localhost', port='5432')
```

Create an instance of `FHIRBase`:
```
fb = fhribase.FHIRBase(connection)
```

Now you can use the following methods of `FHIRBase` instance:
* `.execute(sql, params=None, commit=False)`
* `.execute_without_result(sql, params=None, commit=False)`
* `.row_to_resource(row)`

CRUD methods work with [FHIR resources](https://www.hl7.org/fhir/resourcelist.html).
Resource represented as a dict with specified `resourceType` key as required key.
The following methods works with resource and returns resources.

* `.create(resource, txid=None, commit=True)`
* `.update(resource, txid=None,  commit=True)`
* `.delete(resource, txid=None,  commit=True)`/`.delete(resource_type, id, txid=None, commit=True)`
* `.read(resource)`/`.read(resource_type, id)`
* `.list(sql, params=None)`

# Methods

### .execute
Executes sql with params.

Syntax: `.execute(sql, params=None, commit=False)`

Returns: context manager with cursor as context

Example:
```
with fb.execute('SELECT * FROM patient WHERE id=%s', ['id']) as cursor:
    print(cursor.fetchall())
```

### .execute_without_result
Executes sql with params.

Syntax: `.execute_without_result(sql, params=None, commit=False)`

Returns: nothing

Example:
```
fb.execute_without_result('INSERT INTO transaction (resource) VALUES (%s)', ['{}'])
```

### `.row_to_resource`
Transforms row raw from DB to resource.

Syntax: `.row_to_resource(row)`

Returns: resource representation (dict)

Example:
```
fb.row_to_resource({
    'resource': {'name': []},
    'ts': 'ts',
    'txid': 'txid',
    'resource_type': 'Patient',
    'meta': {'tag': 'created'},
    'id': 'id',
}))
```

will return resource representation:

```
{
    'id': 'id',
    'meta': {'lastUpdated': 'ts', 'versionId': 'txid'},
    'name': [],
    'resourceType': 'Patient',
}
```

### `.create`
Creates resource.
If txid is not specified, new unique logical transaction id will be generated.

Syntax: `.create(resource, txid=None, commit=True)`

Returns: resource representation (dict)

Example:
```
fb.create({
    'resourceType': 'Patient',
    'name': [{'text': 'John'}],
})
```
returns
```
{
    'resourceType': 'Patient',
    'id': 'UNIQUE ID',
    'name': [{'text': 'John'}],
    'meta': {'lastUpdated': 'timestamp', 'versionId': 'txid'},
}
```

### `.update`
Updates resource.
If txid is not specified, new unique logical transaction id will be generated.

Key `id` is required in `resource` argument.

Syntax: `.update(resource, txid=None, commit=True)`

Returns: resource representation (dict)

Example:
```
fb.update({
    'resourceType': 'Patient',
    'id': 'id',
    'name': [{'text': 'John'}],
})
```

returns

```
{
    'resourceType': 'Patient',
    'id': 'UNIQUE ID',
    'name': [{'text': 'John'}],
    'meta': {'lastUpdated': 'timestamp', 'versionId': 'txid'},
}
```


### `.delete`
Deletes resource.
If txid is not specified, new unique logical transaction id will be generated.
Keys `id` and `resourceType` are required in `resource` argument in first variant of usage.

Syntax: `.delete(resource, txid=None, commit=True)` or `.delete(resource_type, id, txid=None, commit=True)`

Returns: nothing

Example:
```
fb.delete({
    'resourceType': 'Patient',
    'id': 'id',
})
```

or

```
fb.delete(resource_type='Patient', id='id')
```


### `.read`
Reads resource.
Keys `id` and `resourceType` are required in `resource` argument in first variant of usage.

Syntax: `.read(resource)` or `.read(resource_type, id)`

Returns: resource representation (dict)

Example:
```
fb.read({
    'resourceType': 'Patient',
    'id': 'id',
})
```

or

```
fb.read(resource_type='Patient', id='id')
```

### `.list`

Executes SQL and returns iterator of resources.
Note: sql query must return all fields of resource table.

Syntax: `.list(sql, params)`

Returns: iterator of resources

Example:
```
for patient in fb.list('SELECT * FROM patient'):
    print(patient)
```

or

```
patients = list(fb.list('SELECT * FROM patient'))
```

# Example application
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
