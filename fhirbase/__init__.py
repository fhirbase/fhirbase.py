import json

from psycopg2.extensions import AsIs
from uuid import uuid4

__version__ = '0.0.1'


class FHIRBaseConnection(object):
    def __init__(self, connection):
        self.connection = connection

    def create_resource(self, txid, **resource):
        try:
            resource_type = resource['resourceType']
        except KeyError:
            raise TypeError(
                '`resource` must contain `resourceType`')

        resource_id = resource.pop('id', None) or str(uuid4())

        cursor = self.connection.cursor()

        cursor.execute(
            '''
            INSERT INTO %(table)s 
                (
                    id, ts, txid, status, resource_type, resource
                )
            VALUES 
                (
                    %(id)s, current_timestamp, %(txid)s, 'created', 
                    %(resource_type)s, %(resource)s
                )
            ON CONFLICT (id) DO UPDATE SET
                txid = %(txid)s, 
                ts = current_timestamp, 
                status = 'recreated',
                resource = %(resource)s
            ''',
            {
                'table': AsIs(resource_type.lower()),
                'id': resource_id,
                'txid': txid,
                'resource_type': resource_type,
                'resource': json.dumps(resource),
            }
        )
        self.connection.commit()
