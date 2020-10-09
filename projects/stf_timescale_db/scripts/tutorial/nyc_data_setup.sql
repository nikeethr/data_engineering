-- double quote for tables/fields
-- single quote for string constants
-- NUMERIC => can be decimal
-- INTEGER => only whole numbers
DROP TABLE IF EXISTS "rides";
CREATE TABLE "rides"(
    vendor_id TEXT,
    pickup_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    dropoff_datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    passenger_count NUMERIC,
    trip_distance NUMERIC,
    pickup_longitude  NUMERIC,
    pickup_latitude   NUMERIC,
    rate_code         INTEGER,
    dropoff_longitude NUMERIC,
    dropoff_latitude  NUMERIC,
    payment_type INTEGER,
    fare_amount NUMERIC,
    extra NUMERIC,
    mta_tax NUMERIC,
    tip_amount NUMERIC,
    tolls_amount NUMERIC,
    improvement_surcharge NUMERIC,
    total_amount NUMERIC
);

-- create a hyper table from the rides table
-- [ ] TODO: test query speeds when space partitioning doesn't exist.
-- (EXPLAIN ANALYZE, maybe ROLLBACK)
-- ANALYZE OPTION allows for query to be executed to get actual speed
/*
SELECT create_hypertable(
    'rides',                   -- table
    'pickup_datetime',         -- timeseries (descending) - main partition
    'payment_type',            -- spartial partition
    2,                         -- no. spatial partitions
    create_default_indexes => FALSE  -- don't create default index tuple for spatial partition
);
*/

-- same as above but no space partition
SELECT create_hypertable('rides', 'pickup_datetime');


-- create a bunch of indices for ease of query
-- [ ] TODO: test speeds when these don't exist.
CREATE INDEX ON rides (vendor_id, pickup_datetime DESC);
CREATE INDEX ON rides (rate_code, pickup_datetime DESC);
CREATE INDEX ON rides (passenger_count, pickup_datetime DESC);

-- create table to handle payment types
-- (sorta like a enum in order not to populate the original table too much)
-- can maybe do this with feature ids with POSTGIS e.g. for catchment/station ids
-- would we query the table first to get the type_idx then do a subsequent
-- query on the main table???
DROP TABLE IF EXISTS "payment_types";
CREATE TABLE IF NOT EXISTS "payment_types"(
    payment_type INTEGER,
    description TEXT
);
INSERT INTO payment_types(payment_type, description) VALUES
(1, 'credit card'),
(2, 'cash'),
(3, 'no charge'),
(4, 'dispute'),
(5, 'unknown'),
(6, 'voided trip');

-- create table to handle rates
DROP TABLE IF EXISTS "rates";
CREATE TABLE IF NOT EXISTS "rates"(
    rate_code   INTEGER,
    description TEXT
);
INSERT INTO rates(rate_code, description) VALUES
(1, 'standard rate'),
(2, 'JFK'),
(3, 'Newark'),
(4, 'Nassau or Westchester'),
(5, 'negotiated fare'),
(6, 'group ride');
