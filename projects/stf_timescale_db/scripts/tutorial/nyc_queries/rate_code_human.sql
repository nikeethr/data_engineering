-- How many rides of each rate type took place?
-- JOIN adds the description column based on the rate index
-- RANK orders by the vendor id, in this case no partition is specified
--  so it will order based on num_trips
SELECT rates.description, COUNT(vendor_id) AS num_trips,
  RANK () OVER (ORDER BY COUNT(vendor_id) DESC) AS trip_rank FROM rides
  JOIN rates ON rides.rate_code = rates.rate_code
  WHERE pickup_datetime < '2016-02-01'
  GROUP BY rates.description
  ORDER BY LOWER(rates.description);

-- efficient version does the group by first before joining
SELECT
    rates.description, t.num_trips,
    RANK() OVER ( ORDER BY t.num_trips DESC ) as trip_rank
FROM rates JOIN
(
    SELECT rate_code, COUNT(vendor_id) AS num_trips
    FROM rides
    WHERE pickup_datetime < '2016-02-01'
    GROUP BY rate_code
) AS t ON t.rate_code = rates.rate_code
ORDER BY LOWER(rates.description);
