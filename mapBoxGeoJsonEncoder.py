class MapBoxGeoJsonEncoder:
    @staticmethod
    def _encodeAsPolygon(lat, lon, lonlatRange):
        return {
            'type': 'Polygon',
            'coordinates': [
                [
                    [round(lon, 6), round(lat, 6)],
                    [round(lon + lonlatRange, 6), round(lat, 6)],
                    [round(lon + lonlatRange, 6), round(lat + lonlatRange, 6)],
                    [round(lon, 6), round(lat + lonlatRange, 6)],
                    [round(lon, 6), round(lat, 6)]
                ]
            ]
        }

    @staticmethod
    def _encodeAsPoint(lat, lon, lonlatRange):
        return {
            'type': 'Point',
            'coordinates': [round(lon + lonlatRange / 2.0, 6), round(lat + lonlatRange / 2.0, 6)]
        }

    @staticmethod
    def encodeSingle(bucket, lonlatRange, asPoint=False):
        if bucket.lonlatRange:
            lonlatRange = bucket.lonlatRange
        return {
            'geometry': MapBoxGeoJsonEncoder._encodeAsPoint(bucket.lat, bucket.lon, lonlatRange) if asPoint else
            MapBoxGeoJsonEncoder._encodeAsPolygon(bucket.lat, bucket.lon, lonlatRange),
            'type': 'Feature',
            'properties': {
                'hourOfDay': bucket.hourOfDay,
                'fare_amounts': bucket.fareAmounts,
                'trip_speed': bucket.tripSpeed,
                'lonlat_range': lonlatRange
            }
        }

    @staticmethod
    def encodeMany(buckets, lonlatRange, asPoints=False):
        return {
            "type": "FeatureCollection",
            "features": [MapBoxGeoJsonEncoder.encodeSingle(b, lonlatRange, asPoints) for b in buckets]
        }
