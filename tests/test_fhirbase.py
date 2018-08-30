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


def test_connect_success(db):
    cur = db.cursor()
    cur.close()


def test_create_success(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})
    if patient.get('id', None) is None:
        pytest.fail('Just created patient should have id')


def test_create_in_transaction_success(db):
    fb = fhirbase.FHIRBase(db)
    txid = fb.start_transaction({'info': 'Create'})

    patient = fb.create({'resourceType': 'Patient'}, txid=txid)

    if int(patient['meta']['versionId']) != txid:
        pytest.fail('Creating does not apply specified txid')


def test_create_failed(db):
    fb = fhirbase.FHIRBase(db)
    with pytest.raises(TypeError):
        fb.create({})


def test_update_success(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})

    patient['name'] = [{'text': 'John'}]
    updated_patient = fb.update(patient)

    if patient['id'] != updated_patient['id']:
        pytest.fail('Patient after updating must have the same id')


def test_update_in_transaction_success(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})

    patient['name'] = [{'text': 'John'}]
    txid = fb.start_transaction({'info': 'Update'})
    updated_patient = fb.update(patient, txid=txid)

    if int(updated_patient['meta']['versionId']) != txid:
        pytest.fail('Updating does not apply specified txid')


def test_update_failed(db):
    fb = fhirbase.FHIRBase(db)
    with pytest.raises(TypeError):
        fb.update({})

    with pytest.raises(TypeError):
        fb.update({'resourceType': 'Patient'})

    with pytest.raises(TypeError):
        fb.update({'id': 'patient'})


def test_read_success(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})

    fetched_patient = fb.read(patient)
    if patient != fetched_patient:
        pytest.fail('Fetched patient must be equal a created patient')


def test_read_by_explicit_ref_success(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})

    fetched_patient = fb.read(patient['resourceType'], patient['id'])
    if patient != fetched_patient:
        pytest.fail('Fetched patient must be equal a created patient')


def test_read_failed(db):
    fb = fhirbase.FHIRBase(db)
    with pytest.raises(TypeError):
        fb.read({})

    with pytest.raises(TypeError):
        fb.read({'resourceType': 'Patient'})

    with pytest.raises(TypeError):
        fb.read({'id': 'patient'})

    with pytest.raises(TypeError):
        fb.read('Patient')


def test_delete_success(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})
    fb.delete(patient)

    fetched_patient = fb.read(patient)
    if fetched_patient is not None:
        pytest.fail('Deleting must remove patient from db')


def test_delete_by_explicit_ref_success(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})
    fb.delete(patient['resourceType'], patient['id'])

    fetched_patient = fb.read(patient)
    if fetched_patient is not None:
        pytest.fail('Deleting must remove patient from db')


def test_delete_in_transaction_success(db):
    fb = fhirbase.FHIRBase(db)
    patient = fb.create({'resourceType': 'Patient'})

    txid = fb.start_transaction({'info': 'Delete'})
    fb.delete(patient, txid=txid)


def test_multiple_operations_in_one_transaction_failed(db):
    fb = fhirbase.FHIRBase(db)
    txid = fb.start_transaction({'info': 'Create and update'})
    patient = fb.create({'resourceType': 'Patient'}, txid=txid)
    updated_patient = fb.update(patient, txid=txid)

    with pytest.raises(psycopg2.DatabaseError):
        fb.delete(patient, txid=txid)
