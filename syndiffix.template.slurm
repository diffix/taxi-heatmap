#!/bin/sh
#SBATCH --time=600
#SBATCH --chdir=/path-to/syndiffix/src/SynDiffix

### IMPORTANT!
#  - Substitute paths to SynDiffix .NET project (above) and files (below) for your own.
#  - `clusters.json` recently used is in the repo root directory.
#  - If you want to run without the facilitated clustering via `clusters.json`, swap this option
#    for `--no-clustering`.

# See `buildMapBox.py` for other instructions.

sha=`git rev-parse --short HEAD`

/usr/bin/time -v \
  dotnet run --configuration Release \
  /path-to/trip_joined_4cols_aid.csv \
  --aidcolumns hack_license \
  --columns pickup_longitude:r pickup_latitude:r fare_amount:r pickup_hour:i \
  --verbose \
  --clusters /path-to/clusters.json \
  > /path-to/trip_joined_4cols_aid.sharp.cluster.custom_cluster-defaultdepth-$sha.csv
