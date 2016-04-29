#!/usr/bin/python3

import gmplot
import json
import ast
import pyproj
from shapely.geometry import LineString, Point
import yattag
import glob
import codecs
from progressbar import ProgressBar, ETA, SimpleProgress, FormatLabel

MAPOUTPUTDIR = 'tfl_bus_routes_maps'

portaljson = json.load(codecs.open('data/london_m25_20160429041218_AllPortals.json', 'r', 'utf-8-sig'))
# we create Point objects now, it saves ~20% of the time per iteration
portals = [Point(x['lngE6']/10.0**6, x['latE6']/10.0**6) for x in portaljson['portals']]

geod = pyproj.Geod(ellps='WGS84')

busroutes = sorted(glob.glob('tfl_bus_routes/*.json'))

results = []

pbar = ProgressBar(widgets=[FormatLabel('Routes processed: %(value)d of %(max)d - '), ETA()],
                   maxval=len(busroutes)).start()

for i, busroute in enumerate(busroutes):

    with open(busroute) as f:
        route = json.load(f)

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
    # fit the map around the bounds of the bus route line
    gmap.fitBounds(line.bounds[1], line.bounds[0], line.bounds[3], line.bounds[2])
    gmap.title = 'Tfl bus: ' + route['lineId'] + ' ' + route['direction']

    gmap.add_symbol('arrowSymbol', {'path': 'google.maps.SymbolPath.FORWARD_CLOSED_ARROW',
                                    'scale': 2})

    gmap.plot(lats, lngs, icons={'icon': 'arrowSymbol', 'offset': '7%', 'repeat': '7%'})

    for port in portals_set:
        gmap.marker(port[1], port[0])
    mapfile = "%s/%s_%s.html" % (MAPOUTPUTDIR, route['lineId'], route['direction'])
    gmap.draw(mapfile)

    results.append([route['lineId'], route['direction'] + ' (' +
                    route['stopPointSequences'][0]['stopPoint'][0]['name'] +
                    ' to ' +
                    route['stopPointSequences'][0]['stopPoint'][-1]['name'] +
                    ')', len(portals_set), mapfile])
    pbar.update(i+1)
pbar.finish()


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
