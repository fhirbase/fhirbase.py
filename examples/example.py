import os
import psycopg2
import fhirbase


def db_connect():
    pguser = os.getenv('PGUSER', 'postgres')
    pgpassword = os.getenv('PGPASSWORD', 'postgres')
    pghost = os.getenv('PGHOST', 'localhost')
    pgport = os.getenv('PGPORT', '5432')
    dbname = os.getenv('PGDATABASE', 'postgres')

    return psycopg2.connect(dbname=dbname, user=pguser,
                            password=pgpassword, host=pghost, port=pgport)


if __name__ == '__main__':
    conn = db_connect()
    try:
        fb = fhirbase.FHIRBase(conn)

        patient = fb.create({'resourceType': 'Patient'})
        print('Created patient: ', patient)

        patient.update({'name': [{'text': 'John'}]})
        updated_patient = fb.update(patient)
        print('Updated patient: ', updated_patient)

        for p in fb.list('select p.* from patient p'):
            print('Patient = ', p)

        fetched_patient = fb.read(patient)
        print('Fetched patient:', fetched_patient)

        fb.delete(patient)
    finally:
        conn.close()
