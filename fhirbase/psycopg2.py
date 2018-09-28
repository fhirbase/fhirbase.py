from contextlib import contextmanager

from psycopg2 import DatabaseError
from psycopg2.extras import Json, DictCursor

__version__ = '0.0.1'


def get_ref(*args):
    """
    Extracts resource type and id from args

    :return: tuple of (resource_type, resource_id)

    >>> get_ref('Patient', 'p1')
    ('Patient', 'p1')

    >>> get_ref({'resourceType': 'Patient', 'id': 'p1'})
    ('Patient', 'p1')

    >>> get_ref()
    Traceback (most recent call last):
    ...
    TypeError: Resource type and id are required

    >>> get_ref('Patient')
    Traceback (most recent call last):
    ...
    TypeError: Resource type and id are required

    >>> get_ref({'resourceType': 'Patient'})
    Traceback (most recent call last):
    ...
    TypeError: First argument must contain `resourceType` and `id` keys
    """
    if len(args) == 1 and isinstance(args[0], dict):
        resource = args[0]

        resource_type = resource.get('resourceType', None)
        resource_id = resource.get('id', None)

        if not resource_type or not resource_id:
            raise TypeError(
                'First argument must contain `resourceType` and `id` keys')
    elif len(args) == 2:
        resource_type = args[0]
        resource_id = args[1]
    else:
        raise TypeError('Resource type and id are required')

    return resource_type, resource_id


def row_to_resource(row):
    """
    Transforms raw row from resource's table to resource representation

    >>> import pprint
    >>> pprint.pprint(row_to_resource({
    ...     'resource': {'name': []},
    ...     'ts': 'ts',
    ...     'txid': 'txid',
    ...     'resource_type': 'Patient',
    ...     'meta': {'tag': 'created'},
    ...     'id': 'id',
    ... }))
    {'id': 'id',
     'meta': {'lastUpdated': 'ts', 'versionId': 'txid'},
     'name': [],
     'resourceType': 'Patient'}
    """
    resource = row['resource']
    meta = row['resource'].get('meta', {})
    meta.update({
        'lastUpdated': row['ts'],
        'versionId': row['txid'],
    })
    resource.update({
        'resourceType': row['resource_type'],
        'id': row['id'],
        'meta': meta,
    })

    return resource


class FHIRBase(object):
    """
    Wrapper for fhirbase connection. Provides CRUD operations on resources.
    """
    def __init__(self, connection):
        self.connection = connection

    def _execute_fn(self, fn_name, params, txid=None, commit=True):
        params = params.copy()

        if txid:
            params.append(txid)

        sql = 'SELECT fhirbase_{fn}({params})'.format(
            fn=fn_name,
            params=','.join(['%s'] * len(params))
        )

        with self.execute(sql, params, commit=commit) as cursor:
            return cursor.fetchone()[0]

    @contextmanager
    def execute(self, sql, params=None, commit=False, *, cursor_factory=None):
        """
        Executes query within cursor's context.
        Returns context manager
        """
        cursor_factory = cursor_factory or DictCursor

        with self.connection.cursor(cursor_factory=cursor_factory) as cursor:
            try:
                cursor.execute(sql, params)
                if commit:
                    self.connection.commit()
                yield cursor
            except DatabaseError:
                self.connection.rollback()
                raise

    def execute_without_result(self, sql, params=None, commit=False):
        """
        Executes query and returns nothing
        """
        with self.execute(sql, params, commit):
            pass

    def start_transaction(self, info=None, *, commit=True):
        """
        Creates new logical transaction and returns id
        """
        info = info or {}

        with self.execute(
                'INSERT INTO transaction (resource) VALUES (%s) RETURNING id',
                [Json(info)],
                commit=commit
        ) as cursor:
            return cursor.fetchone()[0]

    def create(self, resource, *, txid=None, commit=True):
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

        return self._execute_fn('create', [Json(resource)], txid, commit)

    def update(self, resource, *, txid=None, commit=True):
        """
        Updates resource and returns resource.
        If `txid` is not specified, new logical transaction will be created

        Example of usage:
        ```
        fb.update({'resourceType': 'Patient', 'id': 'ID', 'name': []})
        ```
        """
        resource_type, _ = get_ref(resource)

        return self._execute_fn('update', [Json(resource)], txid, commit)

    def delete(self, *args, txid=None, commit=True):
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

        return self._execute_fn(
            'delete', [resource_type, resource_id], txid, commit)

    def read(self, *args):
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

        return self._execute_fn('read', [resource_type, resource_id])

    def list(self, sql, *args):
        """
        Returns iterator of resources`.
        Note: sql should return all fields from resource.

        Example of usage:
        ```
        patients = list(fb.list('SELECT p.* FROM patient p LIMIT 10'))
        ```
        """
        with self.execute(
                'SELECT _fhirbase_to_resource(_result.*) '
                'FROM ({0}) _result'.format(sql),
                *args
        ) as cursor:
            for entry in cursor:
                yield entry[0]

    @classmethod
    def row_to_resource(cls, row):
        return row_to_resource(row)


__all__ = ['FHIRBase', 'row_to_resource']
