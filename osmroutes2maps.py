#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
from collections import defaultdict
from shapely.geometry import LineString, Point
from shapely.ops import linemerge
import gmplot
import urllib
import sys
import codecs
import pyproj
import yattag
import hashlib


routes = defaultdict(list)


osmfile = sys.argv[1]
portalfile = sys.argv[2]
resultdir = sys.argv[3]

portaljson = json.load(codecs.open(portalfile, 'r', 'utf-8-sig'))
# we create Point objects now, it saves ~20% of the time per iteration
portals = [Point(x['lngE6']/10.0**6, x['latE6']/10.0**6) for x in portaljson['portals']]

osm = json.load(open(osmfile))
features = osm['features']

geod = pyproj.Geod(ellps='WGS84')


print('Extacting routes information... ', end='', flush=True)
# extracts all the 'way' features (representing the sections of the route)
# and add them to their relative routes (a way can be part of multiple routes)
for feature in features:
    if feature['id'].startswith('way/'):
        for relation in feature['properties']['@relations']:
            if relation['role'] != 'platform':
                if 'name' in relation['reltags']:
                    routes[relation['reltags']['name']].append(LineString(feature['geometry']['coordinates']))
                else:
                    routes[relation['reltags']['ref']].append(LineString(feature['geometry']['coordinates']))

# merge the segments composing the route
for route in routes:
    routes[route] = linemerge(routes[route])

print('%d routes found' % len(routes), flush=True)

results = []

print('Generating maps', end='', flush=True)
for route in sorted(routes):
    if type(routes[route]) == LineString:
        lines = [routes[route], ]
    else:
        lines = routes[route]

    gmap = gmplot.GoogleMapPlotter(center_lng=lines[0].centroid.x, center_lat=lines[0].centroid.y, zoom=14)

    portals_set = set()

    for line in lines:

        for portal in portals:

            interp = line.interpolate(line.project(portal))

            # https://github.com/mlaloux/My-Python-GIS_StackExchange-answers/blob/master/What%20is%20the%20unit%20the%20shapely%20length%20attribute%3F.md
            angle1, angle2, distance = geod.inv(portal.x, portal.y, interp.x, interp.y)

            if abs(distance) <= 40.0:
                portals_set.add(portal.coords[0])

        lats = [x[1] for x in line.coords]
        lngs = [x[0] for x in line.coords]

        gmap.plot(lats, lngs)
        
        for port in portals_set:
            gmap.marker(port[1], port[0])

    mapfile = '%s.html' % hashlib.sha1(route.encode('utf-8')).hexdigest()
    gmap.draw('%s/%s' % (resultdir, mapfile))

    results.append([route, len(portals_set), mapfile])

    print('.', end='', flush=True)


# generate an html with the results
doc, tag, text = yattag.Doc().tagtext()

with tag('html'):
    with tag('body'):
        with tag('table', border = '1'):
            with tag('tr'):
                with tag('td'):
                    with tag('b'): text('Route')
                with tag('td'):
                    with tag('b'): text('No. of Portals')
                with tag('td'):
                    with tag('b'): text('Link to GMap')
            for route, portals, mapfile in results:
                with tag('tr'):
                    with tag('td'): text(route)
                    with tag('td'): text(str(portals))
                    with tag('td'):
                        with tag('a', target='_blank', href=mapfile):
                            text('Map')

with open('%s/index.html' % resultdir, 'w') as f:
    f.write(doc.getvalue())
