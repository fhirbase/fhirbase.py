#!/bin/bash
set -e

mkdir -p shared
docker-compose up -d
sleep 1  # I don't know why, but it solves a problem with DNS
docker-compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.test.yml run --rm wait_for
docker-compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.test.yml run --rm db fhirbase init 3.0.1
docker-compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.test.yml run --rm tests $@

docker-compose down
