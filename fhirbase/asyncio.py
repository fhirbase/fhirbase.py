from contextlib import asynccontextmanager

from psycopg2 import DatabaseError
from psycopg2.extras import Json, DictCursor

from .utils import get_ref, row_to_resource

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


    async def create(self, resource, *, txid=None, commit=True):
        """
        Creates resource and returns resource.
        If `txid` is not specified, new logical transaction will be created

        Example of usage:
        ```
        fb.create({'resourceType': 'Patient', 'name': []})
        ```
        """
        resource_type = resource.get('resourceType', None)
        if not resource_type:
            raise TypeError('`resource` must contain `resourceType` key')

        return await self._execute_fn('create', [Json(resource)], txid, commit)

    async def update(self, resource, *, txid=None, commit=True):
        """
        Updates resource and returns resource.
        If `txid` is not specified, new logical transaction will be created

        Example of usage:
        ```
        fb.update({'resourceType': 'Patient', 'id': 'ID', 'name': []})
        ```
        """
        resource_type, _ = get_ref(resource)

        return await self._execute_fn('update', [Json(resource)], txid, commit)

    async def delete(self, *args, txid=None, commit=True):
        """
        Deletes resource.
        If `txid` is not specified, new logical transaction will be created

        Example of usage:
        ```
        fb.delete('Patient', 'ID')
        ```
        or
        ```
        fb.delete({'resourceType': 'Patient', 'id': 'ID'})
        ```
        """
        resource_type, resource_id = get_ref(*args)

        return await self._execute_fn(
            'delete', [resource_type, resource_id], txid, commit)

    async def read(self, *args):
        """
        Returns resource or None

        Example of usage:
        ```
        fb.read('Patient', 'ID')
        ```
        or
        ```
        fb.read({'resourceType': 'Patient', 'id': 'ID'})
        ```
        """
        resource_type, resource_id = get_ref(*args)

        return await self._execute_fn('read', [resource_type, resource_id])

    async def list(self, sql, *args):
        """
        Returns iterator of resources`.
        Note: sql should return all fields from resource.

        Example of usage:
        ```
        patients = list(fb.list('SELECT p.* FROM patient p LIMIT 10'))
        ```
        """
        async with self.execute(
                'SELECT _fhirbase_to_resource(_result.*) '
                'FROM ({0}) _result'.format(sql),
                *args
        ) as cursor:
            async for entry in cursor:
                yield entry[0]

    @classmethod
    def row_to_resource(cls, row):
        return row_to_resource(row)


__all__ = ['FHIRBase']
