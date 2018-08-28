from psycopg2 import DatabaseError
from psycopg2.extras import Json

__version__ = '0.0.1'


def get_ref(*args):
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
        raise TypeError('Resource type and id is required')

    return resource_type, resource_id


class FHIRBase(object):
    def __init__(self, connection):
        self.connection = connection

    def _execute(self, sql, params):
        cursor = self.connection.cursor()

        try:
            cursor.execute(sql, params)
            self.connection.commit()

            return cursor.fetchone()[0]
        except DatabaseError:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def _execute_fn(self, fn_name, params, txid=None):
        params = params.copy()

        if txid:
            params.append(txid)

        sql = 'SELECT fhirbase_{fn}({params})'.format(
            fn=fn_name,
            params=','.join(['%s'] * len(params))
        )

        return self._execute(sql, params)

    def start_transaction(self, info=None):
        info = info or {}

        return self._execute(
            'INSERT INTO transaction (resource) VALUES (%s) RETURNING id',
            [Json(info)]
        )

    def create(self, resource, *, txid=None):
        resource_type = resource.get('resourceType', None)
        if not resource_type:
            raise TypeError('`resource` must contain `resourceType` key')

        return self._execute_fn('create', [Json(resource)], txid)

    def update(self, resource, *, txid=None):
        resource_type, _ = get_ref(resource)

        return self._execute_fn('update', [Json(resource)], txid)

    def read(self, *args):
        resource_type, resource_id = get_ref(*args)

        return self._execute_fn('read', [resource_type, resource_id])

    def delete(self, *args, txid=None):
        resource_type, resource_id = get_ref(*args)

        return self._execute_fn('delete', [resource_type, resource_id], txid)


__all__ = ['FHIRBase']
