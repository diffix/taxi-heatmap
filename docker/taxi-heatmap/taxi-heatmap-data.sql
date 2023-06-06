-- This script loads CSV files used by the taxi-heatmap demo

-- The "default" syndiffix result, using column clustering derived by the algorithm
CREATE TABLE syndiffixtaxi (
  pickup_longitude DOUBLE PRECISION,
  pickup_latitude DOUBLE PRECISION,
  fare_amount DOUBLE PRECISION,
  pickup_hour INTEGER
);

COPY syndiffixtaxi(pickup_longitude, pickup_latitude, fare_amount, pickup_hour)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined_4cols_aid.sharp.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

-- A 3-column cluster obtained cheaply by excluding the `fare_amount` column (fill with zeros)
CREATE TABLE syndiffixtaxi_nofare (
  pickup_longitude DOUBLE PRECISION,
  pickup_latitude DOUBLE PRECISION,
  fare_amount DOUBLE PRECISION,
  pickup_hour INTEGER
);

COPY syndiffixtaxi_nofare(pickup_longitude, pickup_latitude, pickup_hour)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined_4cols_aid.lon-lat-hour.sharp.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

UPDATE syndiffixtaxi_nofare
SET fare_amount = 0.0;

-- The "main" syndiffix result obtained on the MPI cluster, using all 4 columns in a single cluster.
CREATE TABLE syndiffixtaxi_full (
  pickup_longitude DOUBLE PRECISION,
  pickup_latitude DOUBLE PRECISION,
  fare_amount DOUBLE PRECISION,
  pickup_hour INTEGER
);

COPY syndiffixtaxi_full(pickup_longitude, pickup_latitude, fare_amount, pickup_hour)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined_4cols_aid.sharp.cluster.12-10000.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

-- Obtained using TVAE from SDV.
CREATE TABLE tvaetaxi (
  pickup_longitude DOUBLE PRECISION,
  pickup_latitude DOUBLE PRECISION,
  fare_amount DOUBLE PRECISION,
  pickup_hour INTEGER
);

COPY tvaetaxi(pickup_longitude, pickup_latitude, fare_amount, pickup_hour)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined_4cols.tvae.epochs300.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

-- Obtained using ctGan from SDV.
CREATE TABLE ctgantaxi (
  pickup_longitude DOUBLE PRECISION,
  pickup_latitude DOUBLE PRECISION,
  fare_amount DOUBLE PRECISION,
  pickup_hour INTEGER
);

COPY ctgantaxi(pickup_longitude, pickup_latitude, fare_amount, pickup_hour)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined_4cols.ctGan.epochs300.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

-- Obtained using mostly.ai.
CREATE TABLE mostlyaitaxi (
  hack_license TEXT,
  pickup_longitude DOUBLE PRECISION,
  pickup_latitude DOUBLE PRECISION,
  fare_amount DOUBLE PRECISION,
  pickup_hour INTEGER
);

COPY mostlyaitaxi(hack_license, pickup_longitude, pickup_latitude, fare_amount, pickup_hour)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined_4cols_aid.mostlyai.epochs200.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

-- The original data which needs to be joined.
-- NOTE: comment out if you want to load the `taxi` table from a file obtained with `taxi-heatmap-prepare.sql`.

COPY trip(medallion, hack_license, vendor_id, rate_code, store_and_fwd_flag, pickup_datetime, dropoff_datetime, passenger_count, trip_time_in_secs, trip_distance, pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_data_1.csv'
(DELIMITER ',', FORCE_NULL (store_and_fwd_flag), FORMAT CSV, HEADER true);

COPY fare(medallion, hack_license, vendor_id, pickup_datetime, payment_type, fare_amount, surcharge, mta_tax, tip_amount, tolls_amount, total_amount)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_fare_1.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

-- The main `taxi` table.
-- NOTE: comment out if you want to load the `taxi` table from a file obtained with `taxi-heatmap-prepare.sql`.
CREATE TABLE taxi AS (SELECT trip.*, fare.payment_type, fare.fare_amount, fare.surcharge, fare.mta_tax, fare.tip_amount, fare.tolls_amount,
                                     fare.total_amount,
                                     substring(trip.pickup_datetime, 12, 2)::integer as pickup_hour
                                     FROM trip, fare 
                                     WHERE trip.medallion=fare.medallion AND
                                           trip.hack_license=fare.hack_license AND
                                           trip.vendor_id=fare.vendor_id AND
                                           trip.pickup_datetime=fare.pickup_datetime AND 
                                           trip.pickup_latitude != 0 AND trip.pickup_longitude != 0 AND
                                           trip.pickup_latitude is not NULL AND trip.pickup_longitude is not NULL AND
                                           fare.fare_amount != 0 AND
                                           trip.trip_distance != 0 AND
                                           trip.trip_time_in_secs != 0 AND
                                           fare.fare_amount is not NULL AND
                                           trip.trip_distance is not NULL AND
                                           trip.trip_time_in_secs is not NULL AND
                                           substring(trip.pickup_datetime, 12, 2)::integer % 4 = 0);

-- The main `taxi` table - load from file version.
-- NOTE: Uncomment if you want to load the `taxi` table from a file obtained with `taxi-heatmap-prepare.sql`.
-- CREATE TABLE taxi (
--   medallion TEXT,
--   hack_license TEXT,
--   vendor_id TEXT,
--   rate_code INTEGER,
--   store_and_fwd_flag TEXT,
--   pickup_datetime TEXT,
--   dropoff_datetime TEXT,
--   passenger_count INTEGER,
--   trip_time_in_secs INTEGER,
--   trip_distance DOUBLE PRECISION,
--   pickup_longitude DOUBLE PRECISION,
--   pickup_latitude DOUBLE PRECISION,
--   dropoff_longitude DOUBLE PRECISION,
--   dropoff_latitude DOUBLE PRECISION,
--   payment_type TEXT,
--   fare_amount DOUBLE PRECISION,
--   surcharge DOUBLE PRECISION,
--   mta_tax DOUBLE PRECISION,
--   tip_amount DOUBLE PRECISION,
--   tolls_amount DOUBLE PRECISION,
--   total_amount DOUBLE PRECISION,
--   pickup_hour INTEGER
-- );

-- COPY taxi(medallion,hack_license,vendor_id,rate_code,store_and_fwd_flag,pickup_datetime,dropoff_datetime,passenger_count,trip_time_in_secs,trip_distance,pickup_longitude,pickup_latitude,dropoff_longitude,dropoff_latitude,payment_type,fare_amount,surcharge,mta_tax,tip_amount,tolls_amount,total_amount,pickup_hour
-- )
-- FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_joined.csv'
-- (DELIMITER ',', FORMAT CSV, HEADER true);
