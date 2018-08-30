# Example

To run example, just do:

```
docker-compose up -d
docker-compose run --rm db fhirbase -d postgres init 3.0.1
docker-compose run --rm example python example.py
```
