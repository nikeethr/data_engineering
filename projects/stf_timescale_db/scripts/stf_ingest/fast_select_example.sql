EXPLAIN ANALYZE
WITH m AS (
    SELECT pk_meta FROM stf_metadata WHERE awrc_id = '403227'
)
SELECT * FROM stf_fc_flow AS f
    WHERE f.meta_id IN (SELECT pk_meta FROM m)
        AND f.fc_datetime = '2020-09-30 23:00Z';

-- OR

EXPLAIN ANALYZE
SELECT f.* FROM stf_fc_flow AS f
INNER JOIN stf_metadata AS m
ON f.meta_id = m.pk_meta AND f.fc_datetime = '2020-09-30 23:00Z' AND m.awrc_id = '403227';

