#!/usr/bin/python3

import json
import gmplot
import sys
import codecs

portalsfile = sys.argv[1]
city = sys.argv[2]

portaljson = json.load(codecs.open(portalsfile, 'r', 'utf-8-sig'))

# portals in ingress are stored multplied by 10^6
points = [(x['latE6']/10.0**6, x['lngE6']/10.0**6) for x in portaljson['portals']]

lats = [x[0] for x in points]
lngs = [x[1] for x in points]

gmap = gmplot.GoogleMapPlotter.from_geocode(city)
gmap.heatmap(lats, lngs, opacity=0.5)

gmap.draw("%s_portals_heatmap.html" % city.lower())
