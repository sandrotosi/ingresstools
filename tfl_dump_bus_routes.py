#!/usr/python/python3
import os.path
import json
import urllib.request
import time

DUMPDIR = 'tfl_bus_routes'

# store here the TfL API key info - 2 vars named app_id and app_key
with open(os.path.expanduser('~/.tfl.json')) as f:
    tflauth = json.load(f)

# this is what needs to be appended to every URL request
urlauth = 'app_id=%s&app_key=%s' % (tflauth['app_id'], tflauth['app_key'])

# get bus routes list
routesreq = urllib.request.urlopen('https://api.tfl.gov.uk/Line/Mode/bus?%s' % urlauth)

routes = json.loads(routesreq.read().decode())

for route in routes:
    for direction in ['inbound', 'outbound']:
        print(route['id'])
        routeinforeq = urllib.request.urlopen('https://api.tfl.gov.uk/line/%s/route/sequence/%s?%s' % (route['id'], direction, urlauth))
        routeinfo = json.loads(routeinforeq.read().decode())
        with open('%s/%s_%s.json' % (DUMPDIR, route['id'], direction), 'w') as f:
            json.dump(routeinfo, f)
        time.sleep(2)
