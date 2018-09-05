import os
import psycopg2
import fhirbase


def db_connect():
    pguser = os.getenv('PGUSER', 'postgres')
    pgpassword = os.getenv('PGPASSWORD', 'postgres')
    pghost = os.getenv('PGHOST', 'localhost')
    pgport = os.getenv('PGPORT', '5432')
    dbname = os.getenv('PGDATABASE', 'fhirbase')

    return psycopg2.connect(dbname=dbname, user=pguser,
                            password=pgpassword, host=pghost, port=pgport)


if __name__ == '__main__':
    conn = db_connect()
    try:
        fb = fhirbase.FHIRBase(conn)

        print('Create patient')
        patient = fb.create({'resourceType': 'Patient'})
        print(patient)

        print()
        print('Update patient')

        patient.update({'name': [{'text': 'John'}]})
        updated_patient = fb.update(patient)
        print(updated_patient)

        print()
        print('List of patients')

        for p in fb.list('SELECT * FROM patient'):
            print(p)

        print()
        print('Custom sql execution')

        query = '''
        SELECT p.resource#>>'{name}' textname 
        FROM patient p
        '''
        with fb.execute(query) as cursor:
            for item in cursor:
                print(item['textname'])

        print()
        print('Read patient')

        fetched_patient = fb.read(patient)
        print(fetched_patient)

        print()
        print('Delete patient')

        fb.delete(patient)
    finally:
        conn.close()
