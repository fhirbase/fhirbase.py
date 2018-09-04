import os

import psycopg2
import pytest

import fhirbase


@pytest.fixture(scope='session')
def db():
    pguser = os.getenv('PGUSER', 'postgres')
    pgpassword = os.getenv('PGPASSWORD', 'postgres')
    pghost = os.getenv('PGHOST', 'localhost')
    pgport = os.getenv('PGPORT', '5432')
    dbname = os.getenv('PGDATABASE', 'postgres')

    return psycopg2.connect(dbname=dbname, user=pguser,
                            password=pgpassword, host=pghost, port=pgport)


@pytest.fixture(scope='function')
def fb(db):
    instance = fhirbase.FHIRBase(db)
    instance.execute_without_result('TRUNCATE TABLE transaction')
    instance.execute_without_result('TRUNCATE TABLE patient')

    return instance


def test_connect_success(db):
    cur = db.cursor()
    cur.close()


def test_list_success(fb):
    fb.create({'resourceType': 'Patient'})
    fb.create({'resourceType': 'Patient'})
    fetched_count = len(list(fb.list('SELECT * from patient')))

    assert fetched_count == 2


def test_execute_success(fb):
    fb.create({'resourceType': 'Patient'})

    with fb.execute('SELECT * from patient') as cursor:
        assert len(cursor.fetchall()) == 1


def test_execute_without_result_with_commit_success(fb):
    fb.execute_without_result(
        'INSERT INTO transaction(resource) VALUES(%s)',
        ['{}'],
        commit=True
    )

    with fb.execute('SELECT * FROM transaction') as cursor:
        assert len(cursor.fetchall()) == 1


def test_execute_without_result_success(fb):
    fb.execute_without_result(
        'INSERT INTO transaction(resource) VALUES(%s)',
        ['{}']
    )

    with fb.execute('SELECT * FROM transaction') as cursor:
        assert len(cursor.fetchall()) == 1


def test_create_success(fb):
    patient = fb.create({'resourceType': 'Patient'})

    assert patient['id'] is not None

    with fb.execute(
            'SELECT * FROM patient WHERE id=%s', [patient['id']]
    ) as cursor:
        assert len(cursor.fetchall()) == 1


def test_create_in_transaction_success(fb):
    txid = fb.start_transaction({'info': 'Create'})

    patient = fb.create({'resourceType': 'Patient'}, txid=txid)

    assert int(patient['meta']['versionId']) == txid


def test_create_failed(fb):
    with pytest.raises(TypeError):
        fb.create({})


def test_update_success(fb):
    patient = fb.create({'resourceType': 'Patient'})

    patient['name'] = [{'text': 'John'}]
    updated_patient = fb.update(patient)

    assert patient['id'] == updated_patient['id']

    with fb.execute(
            'SELECT * FROM patient WHERE id=%s', [patient['id']]
    ) as cursor:
        assert len(cursor.fetchall()) == 1


def test_update_in_transaction_success(fb):
    patient = fb.create({'resourceType': 'Patient'})

    patient['name'] = [{'text': 'John'}]
    txid = fb.start_transaction({'info': 'Update'})
    updated_patient = fb.update(patient, txid=txid)

    assert int(updated_patient['meta']['versionId']) == txid


def test_update_failed(fb):
    with pytest.raises(TypeError):
        fb.update({})

    with pytest.raises(TypeError):
        fb.update({'resourceType': 'Patient'})

    with pytest.raises(TypeError):
        fb.update({'id': 'patient'})


def test_read_success(fb):
    patient = fb.create({'resourceType': 'Patient'})

    fetched_patient = fb.read(patient)
    assert patient == fetched_patient


def test_read_by_explicit_ref_success(fb):
    patient = fb.create({'resourceType': 'Patient'})

    fetched_patient = fb.read(patient['resourceType'], patient['id'])
    assert patient == fetched_patient


def test_read_failed(fb):
    with pytest.raises(TypeError):
        fb.read({})

    with pytest.raises(TypeError):
        fb.read({'resourceType': 'Patient'})

    with pytest.raises(TypeError):
        fb.read({'id': 'patient'})

    with pytest.raises(TypeError):
        fb.read('Patient')


def test_delete_success(fb):
    patient = fb.create({'resourceType': 'Patient'})
    fb.delete(patient)

    with fb.execute(
            'SELECT * FROM patient WHERE id=%s', [patient['id']]
    ) as cursor:
        assert len(cursor.fetchall()) == 0


def test_delete_by_explicit_ref_success(fb):
    patient = fb.create({'resourceType': 'Patient'})
    fb.delete(patient['resourceType'], patient['id'])

    fetched_patient = fb.read(patient)
    assert fetched_patient is None


def test_delete_in_transaction_success(fb):
    patient = fb.create({'resourceType': 'Patient'})

    txid = fb.start_transaction({'info': 'Delete'})
    fb.delete(patient, txid=txid)


def test_multiple_operations_in_one_transaction_failed(fb):
    txid = fb.start_transaction({'info': 'Create and update'})
    patient = fb.create({'resourceType': 'Patient'}, txid=txid)
    patient = fb.update(patient, txid=txid)

    with pytest.raises(psycopg2.DatabaseError):
        fb.delete(patient, txid=txid)


def test_row_to_resource(fb):
    patient = fb.create({'resourceType': 'Patient'})

    with fb.execute('SELECT * FROM patient') as cursor:
        resource = fb.row_to_resource(cursor.fetchone())

        assert resource['id'] == patient['id']
