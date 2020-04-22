#!/usr/bin/python
from configparser import ConfigParser
import psycopg2


def dbconnector(filename='datacrawlers/database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    # connect to the PostgreSQL server
    return psycopg2.connect(**db)


def execute(conn, command):
    try:
        # create a cursor
        cur = conn.cursor()

        # execute a statement
        cur.execute(command)
        conn.commit()
        results = cur.fetchall()
        cur.close()

        # close the communication with the PostgreSQL
        return results
    except (Exception, psycopg2.DatabaseError) as error:
        if 'narusza klucz obcy' not in str(error) and 'no results to fetch' != str(error):
            print(error)
        conn.rollback()
        return None


def select(conn):
    try:

        # create a cursor
        cur = conn.cursor()

        cur.execute("SELECT * FROM public.\"Movie\" where \"ReleaseDate\"::text like '%-01-01'")

        # retrieve the records from the database
        return cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)