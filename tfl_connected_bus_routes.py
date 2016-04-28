#!/usr/bin/python3

import glob
import json
from itertools import combinations
from progressbar import ProgressBar, ETA, SimpleProgress, FormatLabel
import pyproj
import yattag


def three_stops_distance(max_distance, r1_stops, r2_stops):
    """Compare the last/first 2 stops of the 2 routes and return if within DISTANCE"""

    dist = max_distance
    result = None
    
    for r1_stop in r1_stops:
        for r2_stop in r2_stops:
            angle1, angle2, distance = geod.inv(r1_stop['lon'], r1_stop['lat'],
                                                r2_stop['lon'], r2_stop['lat'])
            if distance <= dist:
                dist = distance
                # stopLetter sometimes is missing
                result = (r1_stop['name'], r1_stop.get('stopLetter', ''),
                          round(dist),
                          r2_stop['name'], r2_stop.get('stopLetter', ''))

    return result


DISTANCE = 500 #  meters
MAPSDIR = 'tfl_bus_routes_maps'  # directory containing the bus routes/portals maps

geod = pyproj.Geod(ellps='WGS84')

busroutes = sorted(glob.glob('tfl_bus_routes/*.json'))

# we load the JSONs only once
print('Caching routes JSONs...')
routes = {}
for route in busroutes:
    with open(route) as f:
        routes[route] = json.load(f)
        

pairs = [x for x in combinations(busroutes, 2)]

results = []

pbar = ProgressBar(widgets=[FormatLabel('Pairs processed: %(value)d of %(max)d - '), ETA()],
                   maxval=len(pairs)).start()


for i, (route1, route2) in enumerate(pairs):
    r1 = routes[route1]
    r2 = routes[route2]

    # dont process the same line
    if r1['lineName'] == r2['lineName']:
        continue


        # we first check the end of r1 and the start of r2
    r = three_stops_distance(DISTANCE,
                             r1['stopPointSequences'][0]['stopPoint'][-3:],
                             r2['stopPointSequences'][0]['stopPoint'][:3])
    if r:
        results.append((r1['lineName'], r1['direction'], *r, r2['lineName'], r2['direction']))
    # and then the symmetric relation, the end of r2 and the start of r1
    r = three_stops_distance(DISTANCE,
                             r2['stopPointSequences'][0]['stopPoint'][-3:],
                             r1['stopPointSequences'][0]['stopPoint'][:3])
    if r:
        results.append((r2['lineName'], r2['direction'], *r, r1['lineName'], r1['direction']))

    ## if len(results) > 10:
    ##     break
    
    pbar.update(i+1)
    
pbar.finish()


# generate an html with the results
doc, tag, text = yattag.Doc().tagtext()

with tag('html'):
    with tag('title'):
        text('London TfL connected bus routes (one ends where another starts)')

    with tag('body'):
        with tag('table', border = '1'):
            with tag('tr'):
                with tag('td'):
                    with tag('b'): text('Bus Line Ending')
                with tag('td'):
                    with tag('b'): text('Stop')
                with tag('td'):
                    with tag('b'): text('Distance (m)')
                with tag('td'):
                    with tag('b'): text('Bus Line Starting')
                with tag('td'):
                    with tag('b'): text('Stop')
            for line1, direction1, stop1, stopletter1, distance, stop2, stopletter2, line2, direction2 in sorted(results):
                lett1 = ''
                lett2 = ''
                if stopletter1: lett1 = ' (' + stopletter1 + ')'
                if stopletter2: lett2 = ' (' + stopletter2 + ')'
                with tag('tr'):
                    with tag('td'):
                        with tag('a', target='_blank', href=MAPSDIR+'/'+line1+'_'+direction1+'.html'):
                            text(line1 + ' ' + direction1)
                    with tag('td'): text(stop1 + lett1)
                    with tag('td'): text(distance)
                    with tag('td'):
                        with tag('a', target='_blank', href=MAPSDIR+'/'+line2+'_'+direction2+'.html'):
                            text(line2 + ' ' + direction2)
                    with tag('td'): text(stop2 + lett2)

                    ## With tag('td'):
                    ##     with tag('a', target='_blank', href=mapfile):
                    ##         text('Map')

with open('tfl_connected_bus_routes.html', 'w') as f:
    f.write(doc.getvalue())

print('results written to tfl_connected_bus_routes.html')
