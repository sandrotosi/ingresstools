#!/usr/bin/python3

import glob
import json
import gmplot
import html

MAPSDIR = 'tfl_bus_routes_maps'

busroutes = sorted(glob.glob('tfl_bus_routes/*.json'))

results = []

for busroute in busroutes:
    with open(busroute) as f:
        route = json.load(f)

    first_stop = route['stopPointSequences'][0]['stopPoint'][0]

    stopletter = ''
    if 'stopLetter' in first_stop:
        stopletter = ' (Stop %s)' % first_stop['stopLetter']

    content = """'<h2>%s %s</h2>' +
'<p>%s</p>' +
'<p><a target="_blank", href="%s">see the whole route</a></p>'""" % (route['lineName'], route['direction'],
        html.escape(first_stop['name']+stopletter),
        MAPSDIR+'/'+route['lineName']+'_'+route['direction']+'.html')

    results.append((content, first_stop['lat'], first_stop['lon']))


gmap = gmplot.GoogleMapPlotter.from_geocode('London')
gmap.zoom = 10
# fit the map around the bounds of the bus route line
gmap.title = 'Tfl bus routes first stop'

for result in results:
    gmap.infowindow(*result)

gmap.draw('tfl_bus_routes_first_stop.html')
