class MapBoxGeoJsonEncoder:
    """
    Encodes taxi data bucket results as polygons and points for mapbox to render (GeoJSON).
    """

    @staticmethod
    def encodeMany(buckets, lonlatRange, asPoints=False):
        return {
            "type": "FeatureCollection",
            "features": [MapBoxGeoJsonEncoder._encodeSingle(b, lonlatRange, asPoints) for b in buckets]
        }
    
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
    def _encodeSingle(bucket, lonlatRange, asPoint=False):
        if bucket.lonlatRange:
            lonlatRange = bucket.lonlatRange
        return {
            'geometry': MapBoxGeoJsonEncoder._encodeAsPoint(bucket.lat, bucket.lon, lonlatRange) if asPoint else
            MapBoxGeoJsonEncoder._encodeAsPolygon(bucket.lat, bucket.lon, lonlatRange),
            'type': 'Feature',
            'properties': {
                'hourOfDay': bucket.hourOfDay,
                'fare_amounts': bucket.fareAmounts,
                'lonlat_range': lonlatRange,
                'count': bucket.count
            }
        }
