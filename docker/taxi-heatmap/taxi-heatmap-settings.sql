ALTER USER taxi_heatmap WITH SUPERUSER;
ALTER ROLE taxi_heatmap_publish WITH NOSUPERUSER;

CALL diffix.mark_role('taxi_heatmap_publish', 'anonymized_trusted');
ALTER DATABASE taxi_heatmap SET pg_diffix.compute_suppress_bin = off;
