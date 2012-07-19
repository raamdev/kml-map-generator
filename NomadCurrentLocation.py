import urllib2 # library to do http requests
import urllib # used for urlencode method

# import Raam's GoogleWikipedia module 
from GoogleWikipedia import getGoogleWikipediaArticleURL

# import Raam's GPSToAddress module
from GPSToAddress import convertCoordsToAddress

def nclPublishNewLocation(lat, lon):
	"""
	Publishes new location data to the Nomad Current Location WordPress Plugin
	"""
	
	coordinates = str(lat) + ',' + str(lon)
	
	# set Nomad Current Location API URL and Key
	ncl_url = 'http://raamdev.dev/?'
	ncl_api_key = 'Rsgzau8zSvEKYJw'
	
	# Convert coordinates into textual location (City, State, Country)
	location = convertCoordsToAddress(lat, lon)
	
	# Grab Wikipedia article URL for given location
	wiki_article_url = getGoogleWikipediaArticleURL(location)

	# urlencode query string and build the URL
	f = { 'ncl_api_key' : ncl_api_key, 'location' : location, 'coordinates' : coordinates, 'wiki_url' : wiki_article_url }
	ncl_url = ncl_url + urllib.urlencode(f)
	
	# Call the URL, thereby updating the current location
	urllib2.urlopen(ncl_url)