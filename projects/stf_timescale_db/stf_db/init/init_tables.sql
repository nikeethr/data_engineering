-- extensions:
-- PostGIS
-- TimescaleDB

-- TODO:
-- [x] stf_fc_flow
-- [x] stf_obs_flow
-- [x] stf_metadata
-- [ ] stf_fc_rain (later)
-- [ ] stf_obs_rain (later)
-- geometry -> currently done implicitly via shp2pgsql TODO: explicit?


--- stf_metadata ---
-- TODO:
-- need to expand on this to include more meta data

CREATE TABLE IF NOT EXISTS "stf_metadata" (
    pk_meta         SERIAL PRIMARY KEY,    -- AUTOINCREMENT
    awrc_id         VARCHAR(10) NOT NULL UNIQUE,
    outlet_node     INT NOT NULL,
    catchment       VARCHAR(255) NOT NULL,
    region          VARCHAR(10),
    location        geometry(POINT,4283),  -- TODO: need to check SRID
    station_name    TEXT
);

---

--- stf_obs_flow ---

CREATE TABLE IF NOT EXISTS "stf_obs_flow" (
    obs_datetime TIMESTAMPTZ NOT NULL,
    meta_id      INTEGER NOT NULL,    -- probably not the best name
    value        DOUBLE PRECISION,
    CONSTRAINT fk_meta
        FOREIGN KEY(meta_id)
	    REFERENCES stf_metadata(pk_meta)
);

SELECT create_hypertable(
    'stf_obs_flow',
    'obs_datetime',
    if_not_exists=>True,
    create_default_indexes=>FAlSE
);

DROP INDEX obs_datetime_idx;
DROP INDEX station_id_obs_datetime_idx;
-- ASC is actually not needed here explicitly - it's the default
CREATE INDEX obs_datetime_idx ON stf_obs_flow (obs_datetime ASC);
CREATE UNIQUE INDEX station_id_obs_datetime_idx ON stf_obs_flow (meta_id, obs_datetime ASC);

---

--- stf_fc_flow ---

CREATE TABLE IF NOT EXISTS "stf_fc_flow" (
    fc_datetime     TIMESTAMPTZ NOT NULL,
    lead_time_hours INTEGER NOT NULL,
    meta_id         INTEGER NOT NULL,  -- probably not the best name
    pctl_5          DOUBLE PRECISION,
    pctl_25         DOUBLE PRECISION,
    pctl_50         DOUBLE PRECISION,
    pctl_75         DOUBLE PRECISION,
    pctl_95         DOUBLE PRECISION,
    CONSTRAINT fk_meta
        FOREIGN KEY(meta_id)
	    REFERENCES stf_metadata(pk_meta)
);

SELECT create_hypertable(
    'stf_fc_flow',
    'fc_datetime',
    if_not_exists=>True,
    create_default_indexes=>FAlSE
);

DROP INDEX fc_datetime_idx;
DROP INDEX station_id_fc_datetime_idx;
DROP INDEX station_id_lead_time_hours_fc_datetime_idx;
-- ASC is actually not needed here explicitly - it's the default
CREATE INDEX fc_datetime_idx ON stf_fc_flow (fc_datetime ASC);
CREATE INDEX station_id_fc_datetime_idx ON stf_fc_flow (meta_id, fc_datetime ASC);
-- This one is used mainly for insertion conflicts and searching by lead time
CREATE UNIQUE INDEX station_id_lead_time_hours_fc_datetime_idx
    ON stf_fc_flow(meta_id, lead_time_hours, fc_datetime);
---

