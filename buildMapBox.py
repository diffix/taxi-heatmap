from mapBoxDiffixAccess import MapBoxDiffixAccess
from mapBoxCreator import MapBoxCreator


"""
Create Heatmap from Diffix data
------------------------------

This script queries pg_diffix for bucketized taxi trip data and creates a local web page to view the data on a map.
The map shows a heat map of taxi trips, with exact data once one zooms in.

HowTo:
Make sure you have configured files diffixConfig.py and mapBoxConfig.py in the conf folder. Find your
tokens for mapbox at https://account.mapbox.com/access-tokens/. Your mapbox token must be a public token, secret tokens
won't work. Your default public token is a good choice.

The script requests data from the diffix for differently sized sets of buckets. For each set it creates GeoJSON files
in the www/mapbox/data folder.

All files are served locally and only the default map content (roads, buildings, etc.) are loaded from mapbox.
All diffix data is processed locally in JavaScript.


TlDr;
-----
1. Provision conf/diffixConfig.py and conf/mapBoxConfig.py
2. Put `trip_data_1.csv` and `trip_fare_1.csv` from https://databank.illinois.edu/datasets/IDB-9610843 under `data` subdir in the repo root
3. Build and run the **preparatory** pg_diffix docker image using: (modify your path to the `data` subdir)
```
make taxi-heatmap-prepare-image
docker run --rm --name pg_diffix_taxi_heatmap_prepare -e POSTGRES_PASSWORD=postgres -p 10432:5432 -v path-to-data:/docker-entrypoint-initdb.d/taxi-heatmap/data/ pg_diffix_taxi_heatmap_prepare
```
4. This will produce more CSVs in the `data` subdir, which you should use to run the synthetic data routines. Stop the container.
5. Put the synthetic data CSVs back in the `data` subdir (you can look up the expected names of the CSV files in `taxi-heatmap-data.sql`. Comment out the sources of data which you don't need)
6. Again, build and run docker image:
```
make taxi-heatmap-image
docker run --rm --name pg_diffix_taxi_heatmap -e POSTGRES_PASSWORD=postgres -p 10432:5432 -v path-to-data:/docker-entrypoint-initdb.d/taxi-heatmap/data/ pg_diffix_taxi_heatmap
```
7. Run this file (`buildMapBox.py`) from repository base (from the folder this file is in). If needed update the `baselineTable` to one of the tables containing the baseline data (e.g. `ctgantaxi`)
8. Wait until it outputs "Serving http at port 8000"
9. Point browser to http://localhost:8000/www/mapbox/
"""

title = "NYC taxi trips - Diffix for PostgreSQL"
diffix = MapBoxDiffixAccess()

confLst = list()
geoWidths = [2**-8, 2**-9, 2**-10, 2**-11]
baselineTable = 'mostlyaitaxi'

# 'fir' dropped from the list
for kind in ['raw', 'syndiffix', 'baseline']:
    parentBuckets = None
    for geoWidth in geoWidths:
        buckets = diffix.queryAndStackBuckets(geoWidth, parentBuckets, kind=kind, baselineTable=baselineTable)
        parentBuckets = buckets
        confLst.append(MapBoxCreator.createMap(f"taxi-heatmap-{kind}-{geoWidth}", buckets, geoWidth, kind))
conf = MapBoxCreator.createMergedMap('taxi-heatmap', title, confLst)

MapBoxCreator.serve()
