-- prescribed version
-- For each airport: num trips, avg trip duration, avg cost, avg tip, avg distance, min distance, max distance, avg number of passengers
SELECT rates.description, COUNT(vendor_id) AS num_trips,
   AVG(dropoff_datetime - pickup_datetime) AS avg_trip_duration, AVG(total_amount) AS avg_total,
   AVG(tip_amount) AS avg_tip, MIN(trip_distance) AS min_distance, AVG (trip_distance) AS avg_distance, MAX(trip_distance) AS max_distance,
   AVG(passenger_count) AS avg_passengers
 FROM rides
 JOIN rates ON rides.rate_code = rates.rate_code
 WHERE rides.rate_code IN (2,3) AND pickup_datetime < '2016-02-01'
 GROUP BY rates.description
 ORDER BY rates.description;

-- more efficient version
-- note: rate_code IN (2, 3) makes a big difference compared to
-- rate_code = 2 OR rate_code = 3
SELECT rates.description as trip_desc, t.*
FROM rates JOIN
(
    SELECT
        COUNT(*) as num_trips,
        AVG(dropoff_datetime - pickup_datetime) as avg_trip_duration,
        AVG(total_amount) as avg_cost,
        AVG(tip_amount) as avg_tip,
        MIN(trip_distance) as min_trip_dist,
        MAX(trip_distance) as max_trip_dist,
        AVG(trip_distance) as avg_trip_dist,
        AVG(passenger_count) as avg_passenger_count,
        rate_code
    FROM rides
    WHERE rate_code IN (2,3) AND pickup_datetime < '2016-02-01'
    GROUP BY rate_code
) as t ON rates.rate_code = t.rate_code;
ORDER BY rates.description;
