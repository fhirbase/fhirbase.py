FROM debian:stretch-slim
RUN apt-get update && apt-get install -y wget

# Install fhirbase
RUN wget https://github.com/fhirbase/fhirbase-core/releases/download/nightly-build/fhirbase-linux-amd64 -O /usr/local/bin/fhirbase
RUN chmod +x /usr/local/bin/fhirbase
