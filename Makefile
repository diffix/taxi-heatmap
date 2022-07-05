.PHONY: taxi-heatmap-image pg-diffix-image

taxi-heatmap-image: pg-diffix-base-image
	docker build --target pg_diffix_taxi_heatmap -t pg_diffix_taxi_heatmap .

pg-diffix-base-image:
	docker build --target pg_diffix -t pg_diffix_base_for_taxi_heatmap pg_diffix