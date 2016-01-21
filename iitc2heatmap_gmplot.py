import json
import gmplot

j = json.load(file('portalData/49k_portalData.json'))

# portals in ingress are stored multplied by 10^6
points = [(x[1]['latE6']/10.0**6, x[1]['lngE6']/10.0**6) for x in j.items()]

# rough filter for portals inside the m25
p2 = [x for x in points if 51.443052 < x[0] < 51.611683 and -0.291709 < x[1] < 0.077107]

lats = [x[0] for x in p2]
lngs = [x[1] for x in p2]

gmap = gmplot.GoogleMapPlotter.from_geocode('London')
gmap.heatmap(lats, lngs, opacity=0.5)

gmap.draw("london_portals_heatmap.html")
