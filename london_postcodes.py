import json
import gmplot
import fastkml
import urllib2
import string

# Postcodes info from http://www.doogal.co.uk/london_postcodes.php
# https://en.wikipedia.org/wiki/London_postal_district

TOPLEVELS = {'E': 20, 'N': 22, 'NW': 11, 'SE': 28, 'SW': 20, 'W': 14}

areas  = ['EC', 'WC'] + [x+str(y) for x in TOPLEVELS.keys() for y in range(1, TOPLEVELS[x] + 1)]
areas += ['W1' + x for x in string.uppercase]  # these 2 are special; they'll generate some 404s
areas += ['SW1' + x for x in string.uppercase]
areas += ['E1W', 'N1C', 'N1P', 'NW26']  # special postcodes

gmap = gmplot.GoogleMapPlotter.from_geocode('London')

for area in areas:
    try:
        response = urllib2.urlopen('http://www.doogal.co.uk/kml/%s.kml' % area)
    except Exception, e:
        print 'Error', area, ';', e
        continue
        
    k = fastkml.kml.KML()
    k.from_string(response.read())
    for topcode in k._features[0]._features[0]._features:
        if area in ['WC', 'EC']:
            for postcode in topcode._features:
                zone = postcode.geometry.boundary.xy
                gmap.polygon(zone[1], zone[0])
        else:
            for polygon in topcode.geometry:
                zone = polygon.boundary.xy
                gmap.polygon(zone[1], zone[0])
        #print 'OK', area


gmap.draw("london_postcodes_map.html")
