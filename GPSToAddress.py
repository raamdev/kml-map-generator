# used to parse json data from Google Maps API
try: import simplejson as json
except ImportError: import json

import urllib2 # library to do http requests

def convertCoordsToAddress(lat, lon):
	"""
	Returns "City, ST, Country" for a given lat/lon
	"""
	
	types = ['locality', 'administrative_area_level_1', 'country', 'postal_town']
	location = ""
	city = ""
	state = ""
	country = ""
	
	# Gets json location data for a given lat/lon using the Google Maps API
	# Sourced from http://stackoverflow.com/a/8395513/130664
	def get_geonames(lat, lon, types):
		url = 'http://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&sensor=false' % (lat, lon)
		jsondata = json.load(urllib2.urlopen(url))
		address_comps = jsondata['results'][0]['address_components']
		filter_method = lambda x: len(set(x['types']).intersection(types))
		return filter(filter_method, address_comps)
	
	# Get geographical names
	for geoname in get_geonames(lat, lon, types):
		common_types = set(geoname['types']).intersection(set(types))
		if 'postal_town' in common_types:
			city = geoname['short_name']
		elif 'locality' in common_types:
			city = geoname['short_name']		
		elif 'administrative_area_level_1' in common_types:
			state = geoname['short_name']
		elif 'country' in common_types:
			country = geoname['long_name']	

	# Build locaation using variables that contain data
	for i in [city, state, country]:
		if i != '': location += i + ', '
	
	# Remove extra comma and space from the end if necessary	
	if location.endswith(', '): location = location[:-2]
	
	return location