-- extensions:
-- PostGIS
-- TimescaleDB

-- TODO:
-- stf_obs_flow
-- stf_fc_rain (later)
-- stf_obs_rain (later)
-- metadata
-- geometry


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

--- stf_fc_flow ---

CREATE TABLE IF NOT EXISTS "stf_fc_flow" (
    fc_datetime     TIMESTAMPTZ NOT NULL,
    lead_time_hours INTEGER NOT NULL,
    meta_id         INTEGER NOT NULL,  -- underlying data type for SERIAL?
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

-- ASC is actually not needed here explicitly - it's the default
CREATE INDEX fc_datetime_idx ON stf_fc_flow (fc_datetime ASC);
CREATE INDEX station_id_fc_datetime_idx ON stf_fc_flow (meta_id, fc_datetime ASC);

---

