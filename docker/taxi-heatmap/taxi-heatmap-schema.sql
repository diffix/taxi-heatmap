CREATE TABLE trip (
  medallion TEXT,
  hack_license TEXT,
  vendor_id TEXT,
  rate_code INTEGER,
  store_and_fwd_flag TEXT,
  pickup_datetime TEXT,
  dropoff_datetime TEXT,
  passenger_count INTEGER,
  trip_time_in_secs INTEGER,
  trip_distance DOUBLE PRECISION,
  pickup_longitude DOUBLE PRECISION,
  pickup_latitude DOUBLE PRECISION,
  dropoff_longitude DOUBLE PRECISION,
  dropoff_latitude DOUBLE PRECISION
);

CREATE TABLE fare (
  medallion TEXT,
  hack_license TEXT,
  vendor_id TEXT,
  pickup_datetime TEXT,
  payment_type TEXT,
  fare_amount DOUBLE PRECISION,
  surcharge DOUBLE PRECISION,
  mta_tax DOUBLE PRECISION,
  tip_amount DOUBLE PRECISION,
  tolls_amount DOUBLE PRECISION,
  total_amount DOUBLE PRECISION
);
