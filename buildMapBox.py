from mapBoxDiffixAccess import MapBoxDiffixAccess
from mapBoxCreator import MapBoxCreator


"""
Create Heatmap from Diffix data
------------------------------

This script queries PostgreSQL for bucketized taxi trip data and creates a local web page to view the data on a map.
The map shows a heat map of taxi trips, with exact data once one zooms in. The map is capable of displaying 3
sets of taxi trip data on panes separated by a slider. The usual configuration of the 3 sets is:

`original data | "baseline" (comparison) synthetic data | syndiffix synthetic data`

The PostgreSQL database must be populated with taxi trip data (see instructions below), including synthetic data
from `syndiffix` or any methods we are comparing against. (Formerly the PostgreSQL was querying pg_diffix for data
anonymized using Diffix Fir.)

Make sure you have configured files diffixConfig.py and mapBoxConfig.py in the conf folder. Find your
tokens for mapbox at https://account.mapbox.com/access-tokens/. Your mapbox token must be a public token, secret tokens
won't work. Your default public token is a good choice.

The script requests data for differently sized sets of buckets. For each set it creates GeoJSON files
in the www/mapbox/data folder.

All files are served locally and only the default map content (roads, buildings, etc.) are loaded from mapbox.
All diffix data is processed locally in JavaScript.


Instructions
------------

0. `pip install -r requirements.txt`
1. Provision conf/diffixConfig.py and conf/mapBoxConfig.py according to templates supplied in the same directory
2. Put `trip_data_1.csv` and `trip_fare_1.csv` from https://databank.illinois.edu/datasets/IDB-9610843 under `data` subdir in the repo root
3. Build and run the **preparatory** pg_diffix docker image using: (modify your path to the `data` subdir)
```
make taxi-heatmap-prepare-image
docker run --rm --name pg_diffix_taxi_heatmap_prepare -e POSTGRES_PASSWORD=postgres -p 10432:5432 -v path-to-data:/docker-entrypoint-initdb.d/taxi-heatmap/data/ pg_diffix_taxi_heatmap_prepare
```
This runs some preprocessing steps and produces a single table (CSV file) which can be supplied to external tools, like synthetic data generators (Syndiffix etc.).
4. This will produce more CSVs in the `data` subdir, which you should use to run the synthetic data routines (see syndiffix.template.slurm for the SLURM script used and detailed instructions). Stop the container.
5. Put the synthetic data CSVs back in the `data` subdir (you can look up the expected names of the CSV files in `taxi-heatmap-data.sql`. Comment out the sources of data which you don't need)
6. Again, build and run docker image (note the different `make` target and image name!):
```
make taxi-heatmap-image
docker run --rm --name pg_diffix_taxi_heatmap -e POSTGRES_PASSWORD=postgres -p 10432:5432 -v path-to-data:/docker-entrypoint-initdb.d/taxi-heatmap/data/ pg_diffix_taxi_heatmap
```
7. Run this file (`buildMapBox.py`) from repository base (from the folder this file is in). If needed update the `baselineTable` to one of the tables containing the baseline data (e.g. `ctgantaxi`)
8. Wait until it outputs "Serving http at port 8000"
9. Point browser to http://localhost:8000/www/mapbox/
"""

title = "NYC taxi trips - SynDiffix"
diffix = MapBoxDiffixAccess()

confLst = list()
# The resolution of the buckets with aggregated data. In lon/lat degrees.
geoWidths = [2**-8, 2**-9, 2**-10, 2**-11]
baselineTable = 'mostlyaitaxi'

# 'fir' dropped from the list
for kind in ['raw', 'syndiffix', 'baseline']:
    parentBuckets = None
    for geoWidth in geoWidths:
        # `queryAndStackBuckets` gets new buckets for the current `geoWidth` and combines them with `parentBuckets`
        # to keep the data for a coarser `geoWidth` present. See there for details.
        buckets = diffix.queryAndStackBuckets(geoWidth, parentBuckets, kind=kind, baselineTable=baselineTable)
        parentBuckets = buckets
        confLst.append(MapBoxCreator.createMap(f"taxi-heatmap-{kind}-{geoWidth}", buckets, geoWidth, kind))
conf = MapBoxCreator.createMergedMap('taxi-heatmap', title, confLst)

MapBoxCreator.serve()
