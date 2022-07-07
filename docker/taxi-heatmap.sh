#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE taxi_heatmap;
EOSQL

function sql {
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "taxi_heatmap" "$@"
}

sql -c "CREATE EXTENSION pg_diffix"

sql -f "/docker-entrypoint-initdb.d/taxi-heatmap/taxi-heatmap-schema.sql" \
    -f "/docker-entrypoint-initdb.d/taxi-heatmap/taxi-heatmap-data.sql" \
    -f "/docker-entrypoint-initdb.d/taxi-heatmap/taxi-heatmap-constraints.sql"

taxi_heatmap_password=${taxi_heatmap_PASSWORD:-taxi_heatmap}

sql -c "CREATE USER taxi_heatmap WITH PASSWORD '$taxi_heatmap_password';"
sql -c "CREATE USER taxi_heatmap_publish WITH PASSWORD '$taxi_heatmap_password';"

# Defer setting of access_level to the runtime of the property test
sql <<-EOSQL
  GRANT CONNECT ON DATABASE taxi_heatmap TO taxi_heatmap;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO taxi_heatmap;

  GRANT CONNECT ON DATABASE taxi_heatmap TO taxi_heatmap_publish;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO taxi_heatmap_publish;
EOSQL

# see this file for a TODO, this is a hack
sql -f "/docker-entrypoint-initdb.d/taxi-heatmap/taxi-heatmap-settings.sql"
