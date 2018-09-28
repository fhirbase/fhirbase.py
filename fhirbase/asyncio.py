from contextlib import asynccontextmanager

from psycopg2 import DatabaseError
from psycopg2.extras import Json, DictCursor

class FHIRBase(object):
    """
    Wrapper for fhirbase connection. Provides CRUD operations on resources.
    """
    def __init__(self, connection):
        self.connection = connection

    async def _execute_fn(self, fn_name, params, txid=None, commit=True):
        # TODO handle commit
        params = params.copy()

        if txid:
            params.append(txid)

        sql = 'SELECT fhirbase_{fn}({params})'.format(
            fn=fn_name,
            params=','.join(['%s'] * len(params))
        )

        async with self.connection.cursor() as cursor:
            await cursor.execute(sql, params)
            row = await cursor.fetchone()
            return row[0]

    @asynccontextmanager
    async def execute(self, sql, params=None, commit=False, *, cursor_factory=None):
        """
        TODO handle commit
        Executes query within cursor's context.
        Returns context manager
        """
        cursor_factory = cursor_factory or DictCursor

        async with self.connection.cursor(cursor_factory=cursor_factory) as cursor:
            await cursor.execute(sql, params)
            yield cursor

    async def execute_without_result(self, sql, params=None, commit=False):
        """
        Executes query and returns nothing
        """
        async with self.execute(sql, params, commit):
            pass

    async def start_transaction(self, info=None, *, commit=True):
        """
        Creates new logical transaction and returns id
        """
        info = info or {}

        async with self.execute(
                'INSERT INTO transaction (resource) VALUES (%s) RETURNING id',
                [Json(info)],
                commit=commit
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]

