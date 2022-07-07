import copy

from conf.diffixConfig import DiffixConfig
from sql_adapter import SQLAdapter

def _sql(lonlatRange, countThresh=0):
    return f"""
SELECT {lonlatRange}::float as lonlatRange, *
                    FROM (SELECT
                            diffix.floor_by(pickup_latitude, {lonlatRange}) as lat,
                            diffix.floor_by(pickup_longitude, {lonlatRange}) as lon,
                            substring(pickup_datetime, 12, 2) as hour_of_day,
                            count(*),
                            round((sum(fare_amount) / NULLIF(sum(trip_time_in_secs), 0) * 3600)::numeric, 0)::float8,
                            round((sum(trip_distance) / NULLIF(sum(trip_time_in_secs), 0) * 3600)::numeric, 0)::float8,
                            round(avg(fare_amount)::numeric, 0)::float8 as avg
                            FROM taxi
                            GROUP BY 1, 2, 3) x
WHERE hour_of_day::integer % 4 = 0 AND
      count >= {countThresh} AND
      avg IS NOT NULL;
"""

def _lonlatSteps(start, parentRange, childRange):
    nSteps = round(parentRange / childRange)
    return [start + i * childRange for i in range(0, nSteps)]

# Returns True if the parent bucket as a child with a different value.
def _hasDistinctChild(parentBucket, childRange, bucketsByLatlon):
    for childLat in _lonlatSteps(parentBucket.lat, parentBucket.lonlatRange, childRange):
        for childLon in _lonlatSteps(parentBucket.lon, parentBucket.lonlatRange, childRange):
            childValue = dict.get(bucketsByLatlon, (childLat, childLon, parentBucket.hourOfDay))
            if childValue and childValue != parentBucket.fareAmounts:
                return True
    return False

# Returns True if the parent bucket as any child at all.
def _hasChild(parentBucket, childRange, bucketsByLatlon):
    for childLat in _lonlatSteps(parentBucket.lat, parentBucket.lonlatRange, childRange):
        for childLon in _lonlatSteps(parentBucket.lon, parentBucket.lonlatRange, childRange):
            if (childLat, childLon, parentBucket.hourOfDay) in bucketsByLatlon:
                return True
    return False

def _copyAndSetLonlat(bucket, lat, lon, lonlatRange):
    parentBucketCopy = copy.deepcopy(bucket)
    parentBucketCopy.lat = lat
    parentBucketCopy.lon = lon
    parentBucketCopy.count = None
    parentBucketCopy.lonlatRange = lonlatRange
    return parentBucketCopy


def _putBucket(bucketsByLatlon, bucket):
    bucketsByLatlon[(bucket.lat, bucket.lon, bucket.hourOfDay)] = bucket.fareAmounts


def _appendParentBucket(parentBucket, lonlatRange, buckets, bucketsByLatlon, fillWithSplitBuckets=False):

    noChild = not _hasChild(parentBucket, lonlatRange, bucketsByLatlon)
    if noChild:
        # at this level, the parent has no children whatsoever - we plant the parent and we're done
        buckets.append(parentBucket)
        _putBucket(bucketsByLatlon, parentBucket)
    elif fillWithSplitBuckets:
        # parentBuckets might include "grandparents" of the current generation. In such cases, we still might use the intermediate
        # generations, in case where current generation doesn't appear in the intermediate generation level tiles.
        if parentBucket.lonlatRange > lonlatRange * 2:
            # before we use the children from the current level, let's try an intermediate level
            # First, split the parent into immediate children:
            immediateChildLonlatRange = parentBucket.lonlatRange / 2
            immediateChildren = [_copyAndSetLonlat(parentBucket, lat, lon, immediateChildLonlatRange) for lat, lon in
                                [(parentBucket.lat, parentBucket.lon),
                                (parentBucket.lat + immediateChildLonlatRange, parentBucket.lon),
                                (parentBucket.lat, parentBucket.lon + immediateChildLonlatRange),
                                (parentBucket.lat + immediateChildLonlatRange, parentBucket.lon + immediateChildLonlatRange)]]
            for immediateChild in immediateChildren:
                _appendParentBucket(immediateChild, lonlatRange, buckets, bucketsByLatlon)
        else:
            # Finally we handle at the level of the "finest" ancestors.
            # Handle the special case, where the child that is there is just exactly the same as we're about to fill with.
            # In such case, we prefer to not fill with the parent bucket data, concluding that the parent data is just coming from
            # this single child in 100%
            # NOTE that this only happens in the raw, non-anonymized data. In anonymized data we have noise dependant on the resolution
            # of generalization, so it's unlikely to get a child value exact same as parent's.
            noDistinctChild = not _hasDistinctChild(parentBucket, lonlatRange, bucketsByLatlon)
            if noDistinctChild:
                # leave things as they are
                pass
            else:
                # fill the missing buckets with parent data
                for childLat in _lonlatSteps(parentBucket.lat, parentBucket.lonlatRange, lonlatRange):
                    for childLon in _lonlatSteps(parentBucket.lon, parentBucket.lonlatRange, lonlatRange):
                        if (childLat, childLon, parentBucket.hourOfDay) not in bucketsByLatlon:
                            parentBucketCopy = _copyAndSetLonlat(parentBucket, childLat, childLon, lonlatRange)
                            buckets.append(parentBucketCopy)
                            _putBucket(bucketsByLatlon, parentBucketCopy)
    else:
        pass


class MapBoxDiffixAccess:
    def __init__(self):
        self._sqlAdapter = SQLAdapter(DiffixConfig.parameters)

    def queryAndStackBuckets(self, lonlatRange, parentBuckets, raw=False):
        sql = _sql(lonlatRange, countThresh=5 if raw else 0)
        if raw:
            result = self._sqlAdapter.queryRaw(sql)
        else:
            result = self._sqlAdapter.queryDiffix(sql)

        buckets = []
        for row in result:
            buckets.append(_rowToBucket(row))
        print(f"Loaded {len(buckets)} {'raw' if raw else 'anon'} buckets with range {lonlatRange}.")

        if parentBuckets:
            bucketsByLatlon = {}
            for bucket in buckets:
                _putBucket(bucketsByLatlon, bucket)

            for parentBucket in parentBuckets:
                _appendParentBucket(parentBucket, lonlatRange, buckets, bucketsByLatlon)

        print(f"Combined with parents: {len(buckets)} {'raw' if raw else 'anon'} buckets with range {lonlatRange}.")
        self._sqlAdapter.disconnect()
        return buckets

def _rowToBucket(row):
    lonlatRange = row[0]
    lat = row[1]
    lon = row[2]
    hourOfDay = int(row[3])
    count = row[4]
    hourlyRates = row[5]
    tripSpeed = row[6]
    fareAmounts = row[7]
    return MapBoxBucket(
        lat,
        lon,
        hourOfDay=hourOfDay,
        count=count,
        lonlatRange=lonlatRange,
        hourlyRates=hourlyRates,
        tripSpeed=tripSpeed,
        fareAmounts=fareAmounts
    )


class MapBoxBucket:
    def __init__(self, lat, lon, hourOfDay=None, count=-1, lonlatRange=None, hourlyRates=None, tripSpeed=None, fareAmounts=None):
        self.lat = lat
        self.lon = lon
        self.hourOfDay = hourOfDay
        self.count = count
        self.lonlatRange = lonlatRange
        self.hourlyRates = hourlyRates
        self.tripSpeed = tripSpeed
        self.fareAmounts = fareAmounts

    def __str__(self):
        return f"MapBoxTaxiHeatmap: {self.listOfStrings()}"

    __repr__ = __str__

    def listOfStrings(self):
        return [f"{v}" for v in [self.lat, self.lon, self.hourOfDay, self.count, self.lonlatRange, self.hourlyRates, self.tripSpeed,
                                 self.fareAmounts] if v is not None]
