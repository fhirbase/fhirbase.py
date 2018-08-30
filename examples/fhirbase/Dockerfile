FROM postgres:10.4
RUN apt-get update
RUN apt-get install wget -y

# Install fhirbase
RUN wget https://github.com/fhirbase/fhirbase-core/releases/download/nightly-build/fhirbase-linix-amd64 -O /usr/local/bin/fhirbase
RUN chmod +x /usr/local/bin/fhirbase
