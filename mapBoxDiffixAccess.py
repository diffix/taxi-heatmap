from conf.diffixConfig import DiffixConfig
from sql_adapter import SQLAdapter

def _sql(lonlatRange, kind='raw', baselineTable=None):
    countThresh = 0 if kind in ['fir'] else 5

    table = 'taxi' if kind in ['raw', 'fir'] else 'syndiffixtaxi_full' if kind == 'syndiffix' else baselineTable
    
    return f"""
SELECT {lonlatRange}::float as lonlatRange, *
                    FROM (SELECT
                            diffix.floor_by(pickup_latitude, {lonlatRange}) as lat,
                            diffix.floor_by(pickup_longitude, {lonlatRange}) as lon,
                            pickup_hour,
                            count(*),
                            round(avg(fare_amount)::numeric, 0)::float8 as avg
                            FROM {table}
                            GROUP BY 1, 2, 3) x
WHERE count >= {countThresh} AND
      avg IS NOT NULL;
"""

def _lonlatSteps(start, parentRange, childRange):
    nSteps = round(parentRange / childRange)
    return [start + i * childRange for i in range(0, nSteps)]

# Returns True if the parent bucket as any child at all.
def _hasChild(parentBucket, childRange, bucketsByLatlon):
    for childLat in _lonlatSteps(parentBucket.lat, parentBucket.lonlatRange, childRange):
        for childLon in _lonlatSteps(parentBucket.lon, parentBucket.lonlatRange, childRange):
            if (childLat, childLon, parentBucket.hourOfDay) in bucketsByLatlon:
                return True
    return False


def _putBucket(bucketsByLatlon, bucket):
    bucketsByLatlon[(bucket.lat, bucket.lon, bucket.hourOfDay)] = bucket.fareAmounts


def _appendParentBucket(parentBucket, lonlatRange, buckets, bucketsByLatlon):
    noChild = not _hasChild(parentBucket, lonlatRange, bucketsByLatlon)
    if noChild:
        # at this level, the parent has no children whatsoever - we plant the parent and we're done
        buckets.append(parentBucket)
        _putBucket(bucketsByLatlon, parentBucket)


class MapBoxDiffixAccess:
    def __init__(self):
        self._sqlAdapter = SQLAdapter(DiffixConfig.parameters)

    def queryAndStackBuckets(self, lonlatRange, parentBuckets, kind='raw', baselineTable=None):
        raw = kind == 'raw'

        sql = _sql(lonlatRange, kind=kind, baselineTable=baselineTable)
        if raw:
            result = self._sqlAdapter.queryRaw(sql)
        else:
            result = self._sqlAdapter.queryDiffix(sql)

        buckets = []
        for row in result:
            buckets.append(_rowToBucket(row))
        print(f"Loaded {len(buckets)} buckets with range {lonlatRange} from {kind} data.")

        if parentBuckets:
            bucketsByLatlon = {}
            for bucket in buckets:
                _putBucket(bucketsByLatlon, bucket)

            for parentBucket in parentBuckets:
                _appendParentBucket(parentBucket, lonlatRange, buckets, bucketsByLatlon)

        print(f"Combined with parents: {len(buckets)} buckets with range {lonlatRange} from {kind} data.")
        self._sqlAdapter.disconnect()
        return buckets

def _rowToBucket(row):
    lonlatRange = row[0]
    lat = row[1]
    lon = row[2]
    hourOfDay = int(row[3])
    count = row[4]
    fareAmounts = row[5]
    return MapBoxBucket(
        lat,
        lon,
        hourOfDay=hourOfDay,
        count=count,
        lonlatRange=lonlatRange,
        fareAmounts=fareAmounts
    )


class MapBoxBucket:
    def __init__(self, lat, lon, hourOfDay=None, count=-1, lonlatRange=None, fareAmounts=None):
        self.lat = lat
        self.lon = lon
        self.hourOfDay = hourOfDay
        self.count = count
        self.lonlatRange = lonlatRange
        self.fareAmounts = fareAmounts

    def __str__(self):
        return f"MapBoxTaxiHeatmap: {self.listOfStrings()}"

    __repr__ = __str__

    def listOfStrings(self):
        return [f"{v}" for v in [self.lat, self.lon, self.hourOfDay, self.count, self.lonlatRange,
                                 self.fareAmounts] if v is not None]
