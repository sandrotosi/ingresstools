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
from progressbar import ProgressBar, ETA, SimpleProgress, FormatLabel
import overpy


# this query retrieves all the routes information in te given area of teh city,
# and recursively expand the route (if it starts/ends outside of the area).
# that includes nodes (stops), ways (the streets segments), and relations (the routes)
QUERY = """
[out:json];
area[name = "%(city)s"]->.a;
(
  node["route"="%(type)s"](area.a);
  way["route"="%(type)s"](area.a);
  relation["route"="%(type)s"](area.a);
);
out body;
>;
out skel;
"""


routes = defaultdict(list)


city = sys.argv[1]
routetype = sys.argv[2]
portalfile = sys.argv[3]
resultdir = sys.argv[4]

portaljson = json.load(codecs.open(portalfile, 'r', 'utf-8-sig'))
# we create Point objects now, it saves ~20% of the time per iteration
portals = [Point(x['lngE6']/10.0**6, x['latE6']/10.0**6) for x in portaljson['portals']]


geod = pyproj.Geod(ellps='WGS84')


print('Downloading and parsing routes information... ', end='', flush=True)

api = overpy.Overpass()
osmresult = api.query(QUERY % {'city': city, 'type': routetype})

for relation in osmresult.relations:
    # skip the relation if it has no name associated to it (so no route name)
    if 'name' not in relation.tags:
        continue
    routename = relation.tags['name']
    if 'ref' in relation.tags and not routename.startswith(relation.tags['ref']):
        routename = relation.tags['ref'] + ' ' + routename
    for member in relation.members:
        if member.role == '':
            nodes = member.resolve()
            # just parse the Way objects, which are sections of the route
            if type(nodes) == overpy.Way:
                way = list()
                # The route is composed by several segments, each represented by a Way object
                # we create a LineString for each Way, and we append it to the route ... (1)
                for node in nodes.nodes:
                    way.append((node.lon, node.lat))
                routes[routename].append(LineString(way))

for route in routes:
    # (1) ... and then we merge it in a single line here; it's important to note that
    # linemerge() returns a LineString or MultiLineString when lines are not contiguous
    routes[route] = linemerge(routes[route])

print('%d routes found' % len(routes), flush=True)

results = []

pbar = ProgressBar(widgets=[FormatLabel('Routes processed: %(value)d of %(max)d - '), ETA()],
                    maxval=len(routes)).start()

for i, route in enumerate(sorted(routes)):
    # see above node on linemerge(), we handle the case of MultiLineString by forcing
    # lines to be always a list, eventually made by a single item
    if type(routes[route]) == LineString:
        lines = [routes[route], ]
    else:
        lines = routes[route]

    gmap = gmplot.GoogleMapPlotter(center_lng=lines[0].centroid.x, center_lat=lines[0].centroid.y, zoom=14)
    gmap.fitBounds(routes[route].bounds[1], routes[route].bounds[0],
                   routes[route].bounds[3], routes[route].bounds[2])
    gmap.title = route

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

        gmap.add_symbol('arrowSymbol', {'path': 'google.maps.SymbolPath.FORWARD_CLOSED_ARROW',
                                        'scale': 2})

        if len(line.coords) > 3:
            gmap.plot(lats, lngs , icons={'icon': 'arrowSymbol', 'offset': '7%', 'repeat': '7%'})
        else:
            gmap.plot(lats, lngs)#, icons={'icon': 'arrowSymbol', 'offset': '7%', 'repeat': '7%'})
        
        for port in portals_set:
            gmap.marker(port[1], port[0])

    mapfile = '%s.html' % hashlib.sha1(route.encode('utf-8')).hexdigest()
    gmap.draw('%s/%s' % (resultdir, mapfile))

    results.append([route, len(portals_set), mapfile])

    pbar.update(i+1)
pbar.finish()


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
