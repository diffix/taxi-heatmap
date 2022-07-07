import http.server
import socketserver

"""
Utility to crudely share the heatmap prototype
----------------------------------------------

To view:

1. `cd` into the dir holding this file
2. `python3 serveMapBox.py`
3. Point browser to http://localhost:8000/www/mapbox

To produce the bundle

1. See `buildMapBox.py`
2. Zip this file together with the `www` dir and send
"""

class MapBoxServer:
    @staticmethod
    def serve():
        handler = http.server.SimpleHTTPRequestHandler
        server = socketserver.TCPServer(("", 8000), handler)
        print("--------------------------------------------------")
        print("Serving http at port 8000")
        server.serve_forever()

MapBoxServer.serve()
