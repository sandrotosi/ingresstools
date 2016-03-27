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


# extracts all the 'way' features (representing the sections of the route)
# and add them to their relative routes (a way can be part of multiple routes)
for feature in features:
    if feature['id'].startswith('way/'):
        for relation in feature['properties']['@relations']:
            if relation['role'] != 'platform':
                routes[relation['reltags']['name']].append(LineString(feature['geometry']['coordinates']))

# merge the segments composing the route
for route in routes:
    routes[route] = linemerge(routes[route])
    
for route in sorted(routes):
    print(route)

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

    gmap.draw('%s/%s.html' % (resultdir, urllib.parse.quote(route, safe='')))

