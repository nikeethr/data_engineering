-- How many rides of each rate type took place in the month?
-- Count on vendor_id so that NULL values are not counted

SELECT rate_code, COUNT(vendor_id) AS num_trips
FROM rides
WHERE pickup_datetime < '2016-02-01'
GROUP BY rate_code
ORDER BY rate_code;
