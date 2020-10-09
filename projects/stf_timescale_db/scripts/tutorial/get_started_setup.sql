--- regular sql table

CREATE TABLE IF NOT EXISTS conditions (
  time        TIMESTAMPTZ       NOT NULL,
  location    TEXT              NOT NULL,
  temperature DOUBLE PRECISION  NULL,
  humidity    DOUBLE PRECISION  NULL
);

--- create hyper table partitioned by time
--- TODO: how to partition by composite index?

SELECT create_hypertable('conditions', 'time', if_not_exists => true);

--- INSERT sample
INSERT INTO conditions(time, location, temperature, humidity)
VALUES (NOW(), 'office', 70.0, 50.0);

--- SELECT from table
SELECT * FROM conditions ORDER BY time DESC LIMIT 100;
