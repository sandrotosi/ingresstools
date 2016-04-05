#!/usr/bin/python3

from fastkml import kml
import json
import glob
import ast
from shapely.geometry import LineString


ns = '{http://www.opengis.net/kml/2.2}'
DESTDIR = 'tfl_bus_routes_kml'

busroutes = sorted(glob.glob('tfl_bus_routes/*.json'))

for busroute in busroutes:

    with open(busroute) as f:
        route = json.load(f)

    print('Processing %s %s... ' % (route['lineId'], route['direction']), end="", flush=True)

    l = ast.literal_eval(route['lineStrings'][0])

    line = LineString(l[0])

    k = kml.KML()
    d = kml.Document(ns, 'Tfl Bus route', route['lineId'], "%s %s" %(route['lineId'], route['direction']))
    k.append(d)
    f = kml.Folder(ns, 'fid', 'bus route', '')
    d.append(f)
    p = kml.Placemark(ns, 'id', 'route', '')
    p.geometry = line
    k.append(p)

    with open(DESTDIR + '/' + busroute.replace('tfl_bus_routes/', '').replace('json', 'kml'), 'w') as w:
        w.write(k.to_string(prettyprint=True))
