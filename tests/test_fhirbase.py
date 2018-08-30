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


def test_update(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})

    patient['name'] = [{'text': 'John'}]
    updated_patient = fb.update(patient)

    if patient['id'] != updated_patient['id']:
        pytest.fail('Patient after updating must have the same id')


def test_read(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})

    fetched_patient = fb.read(patient)
    if patient != fetched_patient:
        pytest.fail('Fetched patient must be equal a created patient')


def test_delete(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})
    fb.delete(patient)

    fetched_patient = fb.read(patient)
    if fetched_patient is not None:
        pytest.fail('Deleting must remove patient from db')
