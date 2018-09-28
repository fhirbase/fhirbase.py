import os

import aiopg
import psycopg2
import pytest

import fhirbase.asyncio as fhirbase


@pytest.fixture(scope='function')
async def db():
    pguser = os.getenv('PGUSER', 'postgres')
    pgpassword = os.getenv('PGPASSWORD', 'postgres')
    pghost = os.getenv('PGHOST', 'localhost')
    pgport = os.getenv('PGPORT', '5432')
    dbname = os.getenv('PGDATABASE', 'postgres')

    connection = await aiopg.connect(database=dbname, user=pguser,
                                     password=pgpassword, host=pghost, port=pgport)
    return connection


@pytest.fixture(scope='function')
async def fb(db):
    instance = fhirbase.FHIRBase(db)
    await instance.execute_without_result('TRUNCATE TABLE transaction')
    await instance.execute_without_result('TRUNCATE TABLE patient')

    return instance


@pytest.mark.asyncio
async def test_create_in_transaction_success(fb):
    txid = await fb.start_transaction({'info': 'Create'})
    assert txid is not None
    assert type(txid) == int


@pytest.mark.asyncio
async def test_connect_success(db):
    cur = await db.cursor()
    cur.close()


@pytest.mark.asyncio
async def test_list_success(fb):
    await fb.create({'resourceType': 'Patient'})
    await fb.create({'resourceType': 'Patient'})

    result = []
    async for item in fb.list('SELECT * from patient'):
        result.append(item)
    fetched_count = len(result)

    assert fetched_count == 2


@pytest.mark.asyncio
async def test_execute_success(fb):
    await fb.create({'resourceType': 'Patient'})

    async with fb.execute('SELECT * from patient') as cursor:
        assert len(await cursor.fetchall()) == 1


@pytest.mark.asyncio
async def test_execute_without_result_success(fb):
    await fb.execute_without_result(
        'INSERT INTO transaction(resource) VALUES(%s)',
        ['{}'],
    )

    async with fb.execute('SELECT * FROM transaction') as cursor:
        assert len(await cursor.fetchall()) == 1


@pytest.mark.asyncio
async def test_create_success(fb):
    patient = await fb.create({'resourceType': 'Patient'})

    assert patient['id'] is not None

    async with fb.execute(
            'SELECT * FROM patient WHERE id=%s', [patient['id']]
    ) as cursor:
        assert len(await cursor.fetchall()) == 1


@pytest.mark.asyncio
async def test_create_in_transaction_success(fb):
    txid = await fb.start_transaction({'info': 'Create'})

    patient = await fb.create({'resourceType': 'Patient'}, txid=txid)

    assert int(patient['meta']['versionId']) == txid


@pytest.mark.asyncio
async def test_create_failed(fb):
    with pytest.raises(TypeError):
        await fb.create({})


@pytest.mark.asyncio
async def test_update_success(fb):
    patient = await fb.create({'resourceType': 'Patient'})

    patient['name'] = [{'text': 'John'}]
    updated_patient = await fb.update(patient)

    assert patient['id'] == updated_patient['id']

    async with fb.execute(
            'SELECT * FROM patient WHERE id=%s', [patient['id']]
    ) as cursor:
        assert len(await cursor.fetchall()) == 1


@pytest.mark.asyncio
async def test_update_in_transaction_success(fb):
    patient = await fb.create({'resourceType': 'Patient'})

    patient['name'] = [{'text': 'John'}]
    txid = await fb.start_transaction({'info': 'Update'})
    updated_patient = await fb.update(patient, txid=txid)

    assert int(updated_patient['meta']['versionId']) == txid


@pytest.mark.asyncio
async def test_update_failed(fb):
    with pytest.raises(TypeError):
        await fb.update({})

    with pytest.raises(TypeError):
        await fb.update({'resourceType': 'Patient'})

    with pytest.raises(TypeError):
        await fb.update({'id': 'patient'})


@pytest.mark.asyncio
async def test_read_success(fb):
    patient = await fb.create({'resourceType': 'Patient'})

    fetched_patient = await fb.read(patient)
    assert patient == fetched_patient


@pytest.mark.asyncio
async def test_read_by_explicit_ref_success(fb):
    patient = await fb.create({'resourceType': 'Patient'})

    fetched_patient = await fb.read(patient['resourceType'], patient['id'])
    assert patient == fetched_patient


@pytest.mark.asyncio
async def test_read_failed(fb):
    with pytest.raises(TypeError):
        await fb.read({})

    with pytest.raises(TypeError):
        await fb.read({'resourceType': 'Patient'})

    with pytest.raises(TypeError):
        await fb.read({'id': 'patient'})

    with pytest.raises(TypeError):
        await fb.read('Patient')


@pytest.mark.asyncio
async def test_delete_success(fb):
    patient = await fb.create({'resourceType': 'Patient'})
    await fb.delete(patient)

    async with fb.execute(
            'SELECT * FROM patient WHERE id=%s', [patient['id']]
    ) as cursor:
        assert len(await cursor.fetchall()) == 0


@pytest.mark.asyncio
async def test_delete_by_explicit_ref_success(fb):
    patient = await fb.create({'resourceType': 'Patient'})
    await fb.delete(patient['resourceType'], patient['id'])

    fetched_patient = await fb.read(patient)
    assert fetched_patient is None


@pytest.mark.asyncio
async def test_delete_in_transaction_success(fb):
    patient = await fb.create({'resourceType': 'Patient'})

    txid = await fb.start_transaction({'info': 'Delete'})
    await fb.delete(patient, txid=txid)


@pytest.mark.asyncio
async def test_multiple_operations_in_one_transaction_failed(fb):
    txid = await fb.start_transaction({'info': 'Create and update'})
    patient = await fb.create({'resourceType': 'Patient'}, txid=txid)
    patient = await fb.update(patient, txid=txid)

    with pytest.raises(psycopg2.DatabaseError):
        await fb.delete(patient, txid=txid)


@pytest.mark.asyncio
async def test_row_to_resource(fb):
    patient = await fb.create({'resourceType': 'Patient'})

    async with fb.execute('SELECT * FROM patient') as cursor:
        resource = fb.row_to_resource(await cursor.fetchone())

        assert resource['id'] == patient['id']
