import json
import os
import psycopg2
import configparser
import pprint
import functools
from pgcopy import CopyManager
from timeit import default_timer as timer


DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DIR, "quickstart.cfg")
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)
CONNECTION = "postgres://{user}:{passwd}@{hostname}:{port}/{dbname}".format(
    user=CONFIG["tsdb"]["user"],
    passwd=CONFIG["tsdb"]["passwd"],
    hostname=CONFIG["tsdb"]["hostname"],
    port=CONFIG["tsdb"]["port"],
    dbname=CONFIG["tsdb"]["dbname"]
)


# As per tutorial
def main():
    # conn seems to reference the connection

    # cursor - bound to connection for entire lifetime
    # executed in the context of above database session

    # cursors are not isolated (i.e. other cursors can see the changes
    # within a single connection)

    # cursors are not thread safe

    # similarly sql-alchemy session objects - they should be used in a
    # non-concurrent fashion (one thread at a time)
    # This means all objects that are associated with teh session must be kept
    # within the scope of a single concurrent thread

    # Flask - sqlalcehmy uses a scoped session to handle session lifecycle
    # management for API calls

    # dodgy flag to determine if tables need to be setup or select query need
    # to be executed
    FIRST_TIME = False
    EXECUTE_SAMPLE_QUERY = False

    with psycopg2.connect(CONNECTION) as conn:
        if FIRST_TIME:
            setup_tables(conn)
            populate_sensor_data(conn)

        insert_rows_fast(conn)
        insert_rows(conn)

        if EXECUTE_SAMPLE_QUERY:
            sample_query(conn)

def setup_tables(conn):
    # create sensors table
    # - SERIAL is postgres version of AUTOINCREMENT
    query_create_sensors_table = """
        CREATE TABLE IF NOT EXISTS sensors (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50),
            location VARCHAR(50)
        );
    """

    # create sensor_data table
    query_create_sensordata_table = """
        CREATE TABLE IF NOT EXISTS sensor_data (
            time TIMESTAMPTZ NOT NULL,
            sensor_id INTEGER,
            temperature DOUBLE PRECISION,
            cpu DOUBLE PRECISION,
            FOREIGN KEY (sensor_id) REFERENCES sensors (id)
        );
    """

    # create hypertable
    query_create_sensordata_hypertable = """
        SELECT create_hypertable('sensor_data', 'time', if_not_exists => True);
    """

    # A cursor is a control structure that enables traversal over records
    # in a database
    # enables processing of rows in a result set from a query
    # analogy - pointer to one row in a set of rows in a result set

    # open/close cursor - impicitly done in context
    # [cursor] 1. declare cursor
    # [cursor] 2. fetch/commit - transfer specific row(s) to/from
    #             application
    with conn.cursor() as curs:
        curs.execute(query_create_sensors_table)
        curs.execute(query_create_sensordata_table)
        curs.execute(query_create_sensordata_hypertable)
        conn.commit()


def populate_sensor_data(conn):
    sensors = [
        ("a", "floor"),
        ("a", "ceiling"),
        ("b", "floor"),
        ("b", "ceiling")
    ]
    cur = conn.cursor()

    with conn.cursor() as curs:
        for sensor in sensors:
            try:
                cur.execute(
                    "INSERT INTO sensors (type, location) VALUES (%s, %s);",
                    (sensor[0], sensor[1])
                )
            except (Exception, psycopg2.Error) as error:
               print(error.pgerror)
        conn.commit()


def clean_up_table(conn):
    query_delete_entries = """
        DELETE from sensor_data;
    """
    with conn.cursor() as curs:
        curs.execute(query_delete_entries)
        conn.commit()


def create_dummy_data(conn):
    values = {}
    with conn.cursor() as curs:
       #for sensors with ids 1-4
        for id in range(1,4,1):
            data = (id, )
            #create random data
            simulate_query = """
                SELECT
                generate_series(now() - interval '24 hour', now(), interval '5 minute') AS time,
                %s as sensor_id,
                random()*100 AS temperature,
                random() AS cpu
            """
            curs.execute(simulate_query, data)
            values[id] = curs.fetchall()
    return values


def benchmark_insert(simulate_conflict=False, num_iter=20):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(conn):
            tot = 0
            for i in range(0, num_iter):
                clean_up_table(conn)
                values_current = create_dummy_data(conn)

                if simulate_conflict:
                    # preload data
                    values = create_dummy_data(conn)
                    f(conn, values)
                    # arbitrarily set id=2 to have the same data
                    values_current[2] = values[2]

                start = timer()
                t_offset = f(conn, values_current)
                if t_offset is None:
                    t_offset = 0
                end = timer()
                tot += end - start - t_offset

            print("{}: t = {} sec".format(f.__name__, tot / float(num_iter)))
        return wrapper
    return decorator


def sample_query(conn):
    #query with placeholders
    with conn.cursor() as curs:
        query = """
            SELECT time_bucket('5 minutes', time) AS five_min, avg(cpu)
            FROM sensor_data
            JOIN sensors ON sensors.id = sensor_data.sensor_id
            WHERE sensors.location = %s AND sensors.type = %s
            GROUP BY five_min
            ORDER BY five_min DESC;
        """

        location = "floor"
        sensor_type = "b"
        data = (location, sensor_type)

        curs.execute(query, data)
        results = curs.fetchall()
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(results)


# Benchmark tutorial
# TODO: use decorators to time things and handle cleanup etc.


@benchmark_insert(num_iter=10)
def insert_rows(conn, values):
    # convert values to string
    t_offset = 0
    with conn.cursor() as curs:
        for _, v in values.items():
            start = timer()
            query = """
                INSERT INTO sensor_data (time, sensor_id, temperature, cpu)
                VALUES {};
            """.format(",".join("('{}', '{}', '{}', '{}')".format(*x) for x in v))
            end = timer()
            t_offset += end - start
            curs.execute(query)
        conn.commit()
    print(t_offset)
    return t_offset


@benchmark_insert(num_iter=10)
def insert_rows_fast(conn, values):
    #define columns names of the table you're inserting into
    cols = ("time", "sensor_id", "temperature", "cpu")
    start = timer()
    mgr = CopyManager(conn, "sensor_data", cols)
    end = timer()
    t_offset = end - start

    #create copy manager with the target table and insert!
    for _, v in values.items():
        mgr.copy(v)

    #commit after all sensor data is inserted
    #could also commit after each sensor insert is done
    conn.commit()
    return t_offset

@benchmark_insert(num_iter=10)
def insert_rows_fast(conn, values):
    #define columns names of the table you're inserting into
    cols = ("time", "sensor_id", "temperature", "cpu")
    start = timer()
    mgr = CopyManager(conn, "sensor_data", cols)
    end = timer()
    t_offset = end - start

    #create copy manager with the target table and insert!
    for _, v in values.items():
        mgr.copy(v)

    #commit after all sensor data is inserted
    #could also commit after each sensor insert is done
    conn.commit()
    return t_offset

# TODO: copy from

# Benchmark dataframe
def insert_rows_df_to_sql():
    pass


def insert_rows_df_copy_from():
    pass


def insert_rows_df_copy_manager():
    pass

if __name__ == "__main__":
    main()
