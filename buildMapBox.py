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
3. Build and run the pg_diffix docker image using (modify your path to the `data` subdir)
```
make taxi-heatmap-image
docker run --rm --name pg_diffix_taxi_heatmap -e POSTGRES_PASSWORD=postgres -p 10432:5432 -v path-to-data:/docker-entrypoint-initdb.d/taxi-heatmap/data/ pg_diffix_taxi_heatmap
```
2. Run this file from repository base (from the folder this file is in)
3. Wait until it outputs "Serving http at port 8000"
4. Point browser to http://localhost:8000/www/mapbox/
"""

title = "NYC taxi trips - Diffix for PostgreSQL"
diffix = MapBoxDiffixAccess()

confLst = list()
geoWidths = [2**-8, 2**-9, 2**-10, 2**-11]
parentAnonBuckets = None
parentRawBuckets = None
for geoWidth in geoWidths:
    anonBuckets = diffix.queryAndStackBuckets(geoWidth, parentAnonBuckets)
    parentAnonBuckets = anonBuckets
    confLst.append(MapBoxCreator.createMap(f"taxi-heatmap-{geoWidth}", f"Lat/Lng width: {geoWidth}", anonBuckets, geoWidth))

    rawBuckets = diffix.queryAndStackBuckets(geoWidth, parentRawBuckets, raw=True)
    parentRawBuckets = rawBuckets
    confLst.append(MapBoxCreator.createMap(f"taxi-heatmap-raw-{geoWidth}", f"Non-anonymized data", rawBuckets, geoWidth, raw=True))
conf = MapBoxCreator.createMergedMap('taxi-heatmap', title, confLst)

MapBoxCreator.serve()
