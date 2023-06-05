-- This script is preparing a set of CSV files from the joined taxi table,
-- in order to submit them to our synthetic data generating routines

-- Create CSVs for SynDiffix and oneModel.py (from test-syndiffix) to run on.
COPY taxi(hack_license, pickup_longitude, pickup_latitude, fare_amount, pickup_hour)
TO '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined_4cols_aid.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

COPY taxi(pickup_longitude, pickup_latitude, fare_amount, pickup_hour)
TO '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined_4cols.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

-- Create a CSV of just the AIDs for mostly.ai to process
CREATE TABLE taxi_aids AS (SELECT DISTINCT hack_license FROM taxi);

COPY taxi_aids(hack_license)
TO '/docker-entrypoint-initdb.d/taxi-heatmap/data/taxi_aids.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);
