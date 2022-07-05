FROM pg_diffix_base_for_taxi_heatmap as pg_diffix_taxi_heatmap

COPY docker/taxi-heatmap.sh /docker-entrypoint-initdb.d/
COPY docker/taxi-heatmap /docker-entrypoint-initdb.d/taxi-heatmap
