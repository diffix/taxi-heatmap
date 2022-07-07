import http.server
import json
import os.path
import socketserver
from conf.mapBoxConfig import MapBoxConfig
from mapBoxGeoJsonEncoder import MapBoxGeoJsonEncoder


class MapBoxCreator:
    @staticmethod
    def _writeData(name, buckets, lonlatRange, mapBoxPath):
        dataPath = os.path.join(mapBoxPath, 'data')
        if not os.path.isdir(dataPath):
            os.makedirs(dataPath)
        gjPolygons = MapBoxGeoJsonEncoder.encodeMany(buckets, lonlatRange, asPoints=False)
        polygonsFileRelativePath = os.path.join('data', f"{name}-polygons.geojson")
        with open(os.path.join(mapBoxPath, polygonsFileRelativePath), 'w') as f:
            json.dump(gjPolygons, f)
        gjCenters = MapBoxGeoJsonEncoder.encodeMany(buckets, lonlatRange, asPoints=True)
        centersFileRelativePath = os.path.join('data', f"{name}-centers.geojson")
        with open(os.path.join(mapBoxPath, centersFileRelativePath), 'w') as f:
            json.dump(gjCenters, f)
        return polygonsFileRelativePath, centersFileRelativePath

    @staticmethod
    def createMap(name, subtitle, buckets, lonlatRange, mapBoxPath=None, raw=False):
        if mapBoxPath is None:
            mapBoxPath = os.path.join('www', 'mapbox')
        polygonsFileRelativePath, centersFileRelativePath = MapBoxCreator._writeData(name, buckets, lonlatRange,
                                                                                     mapBoxPath)
        return {
            'name': name,
            'subtitle': subtitle,
            'polygonsFileRelativePath': polygonsFileRelativePath,
            'centersFileRelativePath': centersFileRelativePath,
            'geoWidth': lonlatRange,
            'isRaw': raw,
        }

    @staticmethod
    def createMergedMap(name, title, confLst, mapBoxPath=None):
        if mapBoxPath is None:
            mapBoxPath = os.path.join('www', 'mapbox')
        localConfLst = list()
        for conf in confLst:
            localConf = conf.copy()
            localConfLst.append(localConf)
        conf = {
            'title': title,
            'accessToken': MapBoxConfig.parameters['accessToken'],
            'dataSets': localConfLst,
        }
        confPath = os.path.join(mapBoxPath, 'conf')
        if not os.path.isdir(confPath):
            os.makedirs(confPath)
        confFileRelativePath = os.path.join('conf', f"{name}.json")
        with open(os.path.join(mapBoxPath, confFileRelativePath), 'w') as f:
            json.dump(conf, f)
        return {
            'conf': conf,
            'confFileRelativePath': confFileRelativePath,
        }

    @staticmethod
    def serve():
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", 8000), handler) as httpd:
            print("--------------------------------------------------")
            print(f"Serving http at port 8000")
            httpd.serve_forever()
