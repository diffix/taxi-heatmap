COPY trip(medallion, hack_license, vendor_id, rate_code, store_and_fwd_flag, pickup_datetime, dropoff_datetime, passenger_count, trip_time_in_secs, trip_distance, pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_data_1.csv'
(DELIMITER ',', FORCE_NULL (store_and_fwd_flag), FORMAT CSV, HEADER true);

COPY fare(medallion, hack_license, vendor_id, pickup_datetime, payment_type, fare_amount, surcharge, mta_tax, tip_amount, tolls_amount, total_amount)
FROM '/docker-entrypoint-initdb.d/taxi-heatmap/data/trip_fare_1.csv'
(DELIMITER ',', FORMAT CSV, HEADER true);

CREATE TABLE taxi AS (SELECT trip.*, fare.payment_type, fare.fare_amount, fare.surcharge, fare.mta_tax, fare.tip_amount, fare.tolls_amount,
                                     fare.total_amount,
                                     trip.trip_distance / trip.trip_time_in_secs * 3600 as trip_speed_mph FROM trip, fare 
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
