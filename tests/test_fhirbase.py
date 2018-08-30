import os

import psycopg2
import pytest

import fhirbase


@pytest.fixture
def db():
    pguser = os.getenv('PGUSER', 'postgres')
    pgpassword = os.getenv('PGPASSWORD', 'postgres')
    pghost = os.getenv('PGHOST', 'localhost')
    pgport = os.getenv('PGPORT', '5432')
    dbname = os.getenv('PGDATABASE', 'postgres')

    return psycopg2.connect(dbname=dbname, user=pguser,
                            password=pgpassword, host=pghost, port=pgport)


def test_connect(db):
    cur = db.cursor()
    cur.close()


def test_create(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})
    if patient.get('id', None) is None:
        pytest.fail('Just created patient should have id')
