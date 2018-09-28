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

