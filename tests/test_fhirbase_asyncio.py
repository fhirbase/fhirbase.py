import os

import aiopg
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

