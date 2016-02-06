#!/usr/bin/python3

import gmplot
import json
import ast
import pyproj
from shapely.geometry import LineString, Point
import time
# local copy from https://pypi.python.org/pypi/yattag
import yattag
import glob

MAPOUTPUTDIR = 'tfl_bus_routes_maps'

with open('portalData/49k_portalData.json') as f:
    j = json.load(f)

# we create Point objects now, it saves ~20% of the time per iteration
portals = [Point(x[1]['lngE6']/10.0**6, x[1]['latE6']/10.0**6) for x in j.items()]

geod = pyproj.Geod(ellps='WGS84')

start = end = 0

#busroutes = ['tfl_bus_routes/309_outbound.json', 'tfl_bus_routes/309_inbound.json']
busroutes = sorted(glob.glob('tfl_bus_routes/*.json'))

results = []

for busroute in busroutes:

    start = time.time()

    with open(busroute) as f:
        route = json.load(f)

    print('Processing %s %s... ' % (route['lineId'], route['direction']), end="", flush=True)

    # lineString is a Unicode string containing a list of pairs, for the points
    # on the map drawing a line the bus takes on the streets, so need to convert
    # that string into a python datatype
    l = ast.literal_eval(route['lineStrings'][0])

    line = LineString(l[0])

    portals_set = set()

    for portal in portals:

        interp = line.interpolate(line.project(portal))

        # https://github.com/mlaloux/My-Python-GIS_StackExchange-answers/blob/master/What%20is%20the%20unit%20the%20shapely%20length%20attribute%3F.md
        angle1, angle2, distance = geod.inv(portal.x, portal.y, interp.x, interp.y)

        if abs(distance) <= 40.0:
            portals_set.add(portal.coords[0])

    lats = [x[1] for x in l[0]]
    lngs = [x[0] for x in l[0]]

    # center the map around the "centroid" of the bus route
    gmap = gmplot.GoogleMapPlotter(center_lng=line.centroid.x, center_lat=line.centroid.y, zoom=14)
    # TODO: fitBounds()/getBounds() https://developers.google.com/maps/documentation/javascript/reference [to set the zoom more accurately]
    gmap.plot(lats, lngs)
    for port in portals_set:
        gmap.marker(port[1], port[0])
    mapfile = "%s/%s_%s.html" % (MAPOUTPUTDIR, route['lineId'], route['direction'])
    gmap.draw(mapfile)

    end = time.time()

    print('done: portals found = %d, time = %fs' % (len(portals_set), end - start))

    results.append([route['lineId'], route['direction'] + ' (' +
                    route['stopPointSequences'][0]['stopPoint'][0]['name'] +
                    ' to ' +
                    route['stopPointSequences'][0]['stopPoint'][-1]['name'] +
                    ')', len(portals_set), mapfile])


# generate an html with the results
doc, tag, text = yattag.Doc().tagtext()

with tag('html'):
    with tag('title'):
        text('London TfL bus routes and portals in their range')

    with tag('body'):
        with tag('table', border = '1'):
            with tag('tr'):
                with tag('td'):
                    with tag('b'): text('Bus Line')
                with tag('td'):
                    with tag('b'): text('Direction')
                with tag('td'):
                    with tag('b'): text('No. of Portals')
                with tag('td'):
                    with tag('b'): text('Link to GMap')
            for line, direction, portls, mapfile in results:
                with tag('tr'):
                    with tag('td'): text(line)
                    with tag('td'): text(direction)
                    with tag('td'): text(str(portls))
                    with tag('td'):
                        with tag('a', target='_blank', href=mapfile):
                            text('Map')

with open('tfl_bus_routes_maps.html', 'w') as f:
    f.write(doc.getvalue())

print('results written to tfl_bus_routes_maps.html')
