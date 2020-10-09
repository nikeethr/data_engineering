SELECT date_trunc('day', pickup_datetime) as day, COUNT(*)
FROM rides GROUP BY day ORDER BY day;
