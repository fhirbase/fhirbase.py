#!/bin/bash
docker-compose up -d
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm wait_for
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm db fhirbase init 3.0.1
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm tests $@
bash <(curl -s https://codecov.io/bash)
