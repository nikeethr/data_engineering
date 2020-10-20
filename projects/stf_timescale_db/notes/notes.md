# Timescale DB

## Rough notes

### General TODO

- [x] setup timescaledb + docker
- [x] Go through starter tutorial
- [ ] Investigate python implementation to copy over data
- [ ] Investigate SQLAlchemy for db model
- [ ] Benchmark copying of data into database (+ duplicate avoiding)
- [ ] Process and insert sample stf time-series file
- [ ] Process and insert shape files/geojson files in POSTGIS
- [ ] Go through visualisation tutorial (Grafana)
- [ ] Make app with some controls to display the data
- [ ] Optimization - compression policy, partitioning, table spaces etc.

**Nice to do**

- Try with all ensemble members

### Installing timescale DB - Docker

- Followed instructions in:

  https://docs.timescale.com/latest/getting-started/installation/docker/installation-docker

- Had to update docker-compose to expose the right ports, env file etc. etc.
- Had to reinstall postgressql-12 as it didn't work with Debian 10 (which had
  postgresql-11):

  https://www.postgresql.org/download/linux/debian/

### Starter tutorial

- [setup db](https://docs.timescale.com/latest/getting-started/setup)
- [create hypertable](https://docs.timescale.com/latest/getting-started/creating-hypertables)
- [hello world](https://docs.timescale.com/latest/tutorials/tutorial-hello-timescale)
- [python](https://docs.timescale.com/latest/tutorials/quickstart-python)
- [tuning DB](https://docs.timescale.com/latest/getting-started/configuring)
- [nyc taxi trips](https://docs.timescale.com/latest/tutorials/tutorial-hello-timescale)
- switched off telemetry

#### Hello world

**location**: `./scripts/nyc_data*`

##### PostGIS

```
CREATE EXTENSION postgis;
```

##### Tests/benchmarking

**Tutorial Queries**

```sql
SELECT date_trunc('day', pickup_datetime) as day, COUNT(*)
FROM rides GROUP BY day ORDER by day;
```

`execution_time=26s`

- Noticed 2/12 chunk split:
    - potentially because timeframe is a month and data has 12 months (2016)
      the 2 indicates spatial split maybe?
- Most of the execution was from gathering the data, and the trunctation
  operation. As opposed to the group by etc.

```sql
SELECT date_trunc('day', pickup_datetime) AS day, avg(fare_amount)
FROM rides
WHERE passenger_count = 1
AND pickup_datetime < '2016-01-08'
GROUP BY day ORDER BY day;
```

`execution_time=6s`

- Does a scan backward from the middle chunk to check where the data might be
  from halfway point (chunk 5&6) - due to parallel workers
- Based on knowledge of chunk interval computes likely chunks where the data
  will reside?
- Up to this point its about 400ms after the chunks are found
- Again, searching for the entries seems to take most of the time.
- Upon testing using `SELECT show_chunks(older_than => TIMESTAMP <ts>)` I was
  able to determine that the chunking may have been altered due to
  `payment_type` being in the mix... due to spatial partitioning - still only
  one chunk set was exposed e.g. `_hyper_2_1_chunk`. This could either mean:
    A. chunks were not spatially partitioned OR
    B. only one table space is exposed so only can see one set of chunks...
    
```sql
SELECT chunk_table, partitioning_columns, ranges
FROM chunk_relation_size_pretty('rides');
```
- Gives the chunk ranges, seems like it has been set to 7 days.
- I was wrong in the assumption - data set is actually only one month (plus a
  few outlier days in 2017 for some reason) - which made me think it was 12
  months.
- The hypertable chunks had 12 chunks because:
`(5 weeks x 2 space partitions chunks) + (1 x 2 chunks from outlier dates)`

```sql
SELECT rate_code, COUNT(vendor_id) AS num_trips
FROM rides
WHERE pickup_datetime < '2016-02-01'
GROUP BY rate_code
ORDER BY rate_code;
```

`execution_time=22s`

- This is done for the entire month so expected to be a bit slower.
- Note: it didn't seem that slow - maybe due to parallel processing??

```sql
SELECT rates.description, COUNT(vendor_id) AS num_trips,
  RANK () OVER (ORDER BY COUNT(vendor_id) DESC) AS trip_rank FROM rides
  JOIN rates ON rides.rate_code = rates.rate_code
  WHERE pickup_datetime < '2016-02-01'
  GROUP BY rates.description
  ORDER BY LOWER(rates.description);
```

`execution_time=66s`
`execution_time=22s` (efficient version - same as above)

- This is a 'nicer' version about the above query in terms of human readibilty
  of the output. However runtime is quite slow.
- I think the issue is due to it doing a split in parallel and then merge
  (causing multiple sorts as well as disk merge.)
- A more efficient query where the selection is done before the join can be
  found in `scripts/tutorial/nyc_queries/rate_code_huamn.sql`

**Test 1: space partitioning**

- A: QUERY with space partitioning
- B: QUERY without space partitioning

**Test 2: indexing**

- A: QUERY on `pickup_datetime` then `vendor_id`
- B: QUERY on `vendeor_id` then `pickup_datetime`
- C: Remove composite index and QUERY

**Test 3: no timescaledb**

- A: QUERY with hypertable
- B: QUERY without hypertables

**Test 4: change ORDER/SORT**

- A: QUERY without SORT
- B: QUERY with SORT (in a direction that does something)


#### Useful commands

> Add as I go...

**psql specific**

```
\l     => show databases
\c db  => choose (use) database
\d tb  => describe table (\d on it's own will list the tables)
\dx    => describe extensions
\x     => toggle expanded display
```

**vanilla sql**

```
-- create database
CREATE database <db>;

-- create hyper table based on certain index
SELECT create_hypertable(<tb>, <index>);

-- count entries in table
SELECT COUNT(*) FROM <tb>;

-- truncate date
date_trunc('day', pickup_datetime) as day

-- :: is casting index e.g.:
SELECT 0.9::text;
SELECT 'POINT(0 0)'::geometry;
```

**sample queries**

```sql
-- select truncated date (by day) and the count for each entry
-- grouped by the day
SELECT date_trunc('day', pickup_datetime) as day, COUNT(*)
FROM rides GROUP BY day ORDER by day;
```

### python + tsdb

- [quick start](https://docs.timescale.com/latest/tutorials/quickstart-python)
- sqlalchemy for data model `--> TODO: link`

#### script location

```
stf_tsdb/scripts/python-quickstart
```

need to configure `quickstart.cfg` to set the database connections params.


### stf ingest

#### script location

```
stf_tsdb/scripts/stf_ingest
```

#### conda env

Installed the following:

```
psycopg2
gdal
pgcopy
```

**WARNING:** The above packages may have installed posgres=11 on the env. This
will cause issues when trying to access the database via `psql`. As the tsdb is
currently using posgres=12. May consider downgrading for deployment.

#### Shape files

You can use `shp2pgsql` to copy shape files to postgis.
    - Wrote a script to do this. For now a script is fine since the shape files
      are most likely one-off things rather than constant updates. Can port to
      python workflow later if needed.

### grafana + tsdb

### continuous aggregates (for e.g. daily data)

- can use integer division for this

## Background reading

- indexing: useful for creating composite indices
    - https://docs.timescale.com/latest/using-timescaledb/schema-management
    - https://www.postgresql.org/docs/current/indexes-intro.html
- query optimization:
    - https://www.postgresql.org/docs/latest/sql-explain.html


## Random dump

Insert pandas dataframe:
https://naysan.ca/2020/06/21/pandas-to-postgresql-using-psycopg2-copy_from/

copy manager:
https://docs.timescale.com/latest/tutorials/quickstart-python#new_database
