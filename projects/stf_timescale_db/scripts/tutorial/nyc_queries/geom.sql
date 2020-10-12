-- 2163 = metres in US region
ALTER TABLE rides ADD COLUMN IF NOT EXISTS pickup_geom geometry(POINT, 2163);
ALTER TABLE rides ADD COLUMN IF NOT EXISTS dropoff_geom geometry(POINT, 2163);

-- transform from global lat/lon coordinate system to metres within US region
-- note: These are geometry coordinates (cartesian)
-- this ensures that queries are faster, but need to understand the usecase for
-- geography cordinates as well
UPDATE rides SET
    pickup_geom = ST_Transform(ST_SetSRID(ST_MakePoint(pickup_longitude, pickup_latitude), 4326), 2163),
    dropoff_geom = ST_Transform(ST_SetSRID(ST_MakePoint(dropoff_longitude, dropoff_latitude), 4326), 2163);

-- How many taxis pick up rides within 400m of Times Square on New Years Day, grouped by 30 minute buckets.
-- Number of rides on New Years Day originating within 400m of Times Square, by 30 min buckets
-- Note: Times Square is at (lat, long) (40.7589,-73.9851)

-- 2064ms with `ST_DWithin`
-- 1946ms with `ST_Distance`

SELECT COUNT(*), time_bucket('30 minutes', pickup_datetime) AS thirty_min
FROM rides
WHERE ST_Distance(ST_Transform(ST_GeomFromEWKT('SRID=4326;POINT(-73.9851 40.7589)'), 2163), pickup_geom) < 400
AND pickup_datetime < '2016-01-01 14:00'
GROUP BY thirty_min ORDER BY thirty_min;
