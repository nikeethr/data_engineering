-- stf_fc_flow
-- stf_obs_flow
-- stf_fc_rain (later)
-- stf_obs_rain (later)

CREATE TABLE IF NOT EXISTS "stf_fc_flow" (
    fc_datetime TIMESTAMPTZ NOT NULL,
    lead_time_hours INTEGER NOT NULL,
    awrc_id VARCHAR(10) NOT NULL,
    pctl_5  DOUBLE PRECISION,
    pctl_25 DOUBLE PRECISION,
    pctl_50 DOUBLE PRECISION,
    pctl_75 DOUBLE PRECISION,
    pctl_95 DOUBLE PRECISION
);

SELECT create_hypertable(
    'stf_fc_flow',
    'fc_datetime',
    if_not_exists=>True,
    create_default_indexes=>FAlSE
);

--- ASC is actually not needed here explicitly - it's the default
CREATE INDEX fc_datetime_idx ON stf_fc_flow (fc_datetime ASC);
CREATE INDEX station_id_fc_datetime_idx ON stf_fc_flow (awrc_id, fc_datetime ASC);
