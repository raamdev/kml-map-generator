import datetime
import time # used for getting local timezone offset to convert to UTC
import xml.dom.minidom as DOM
from xml.dom.minidom import parseString
from dateutil.parser import parse

import urllib2 # library to do http requests
import urllib # used for urlencode method

# import Raam's GoogleWikipedia module 
from GoogleWikipedia import getGoogleWikipediaArticleURL

# import Raam's GPSToAddress module
from GPSToAddress import convertCoordsToAddress

# import Raam's NomadCurrentLocation module
from NomadCurrentLocation import nclPublishNewLocation

# -------------------------------------------------------

now = datetime.datetime.now()
print "\n\n> Started processing on " + now.strftime("%Y-%m-%d %H:%M:%S")

# -------------------------------------------------------

pathPlacemarkName = 'Path' # this is the name of the Placemark in current_kml_file that includes a LineString of the path

# URL to your Foursquare KML feed (login to Foursquare and visit https://feeds.foursquare.com/history/)
foursquare_kml_url = 'https://feeds.foursquare.com/history/NAWZJFBHVAUBTCOWGIH5XMNZ1M3QXLMI.kml'

# KML file that we're updating; new Foursquare placemarks will be appended here
current_kml_file = 'current_sample.kml'

newPlacemarks = 0
skippedPlacemarks = 0

# -------------------------------------------------------	

def updateStats(statType):
	"""
	Updates simple statistics about how many placemarks were processed
	"""
	
	global newPlacemarks
	global skippedPlacemarks
	
	if statType == 'new':
		newPlacemarks += 1
	
	if statType == 'skipped':
		skippedPlacemarks += 1

def stripTags(string, startTag, endTag):
	"""
	Strips startTag and endTag from string
	"""
	
	return string.replace(startTag,'').replace(endTag,'')
	
def updateCurrentLocation(currentBaseFolder):
	"""
	Updates the 'Current Location' text on the latest Placemark
	"""
	
	isNewestPlacemark = False
	
	newest_placemark_date = getNewestPublishedPlacemarkDate(currentBaseFolder)
	
	# loop through placemarks looking for the <published> elemement that matches date of newest_placemark_date
	for placemark in currentBaseFolder.getElementsByTagName("Placemark"):
		for node in placemark.getElementsByTagName("published"):
			placemarkDate = parse(node.firstChild.wholeText).strftime('%s')			
			placemarkDate = int(placemarkDate)
			if placemarkDate == newest_placemark_date:
				isNewestPlacemark = True
			else:
				isNewestPlacemark = False

		# if this is the placemark that needs "Current Location: " prefixed to the <description>
		if isNewestPlacemark:
			if placemark.getElementsByTagName("description"):
				description = placemark.getElementsByTagName("description")
				for desc in description:
					orig_desc = desc.firstChild.wholeText.strip()
					if not orig_desc.startswith("Current Location: "):	
						desc.firstChild.replaceWholeText("Current Location: " + orig_desc)
						print ">> Updated Current Location to '%s'" % desc.firstChild.wholeText.strip()
			
			# Grab the updated date and convert it to Unixtime in UTC
			if placemark.getElementsByTagName("updated"):
				updated_date = placemark.getElementsByTagName("updated")
				for date in updated_date:
					date_offset = time.timezone
					new_date = parse(date.firstChild.wholeText).strftime('%s')
					new_date = int(new_date) - date_offset

			# Grab the coordinates for this placemark 			
			pointElements = placemark.getElementsByTagName("Point")
			for point in pointElements:
				newPlacemarkCoordinates = point.getElementsByTagName("coordinates")[0].firstChild.wholeText.strip()
				newLatLon = newPlacemarkCoordinates.split(',')
				new_lon = newLatLon[0]
				new_lat = newLatLon[1]
				print ">> Updating WordPress Current Location plugin with new placemark coordinates: lon=%s lat=%s" % (new_lon, new_lat)
				nclPublishNewLocation(new_lat, new_lon, new_date)
		else:
			# remove "Current Location: " from this description if necessary
			if placemark.getElementsByTagName("description"):				
				description = placemark.getElementsByTagName("description")
				for desc in description:
					orig_desc = desc.firstChild.wholeText.strip()
					if orig_desc.startswith("Current Location: "):
						desc.firstChild.replaceWholeText(desc.firstChild.wholeText.strip().replace("Current Location: ", ''))
						print ">> Removed old Current Location from '%s'" % desc.firstChild.wholeText
	
def getNewestPublishedPlacemarkDate(currentBaseFolder):
	"""
	search currentBaseFolder <Placemark>'s for newest <published> date
	"""
	
	newest_date = 0
	
	# loop through placemarks looking for <published> elemements
	for placemark in currentBaseFolder.getElementsByTagName("Placemark"):
		for node in placemark.getElementsByTagName("published"):
			placemarkDate = parse(node.firstChild.wholeText).strftime('%s')
			
			placemarkDate = int(placemarkDate)
			if placemarkDate > newest_date:
				newest_date = placemarkDate
				
	print '>> Found newest Placemark date from %r: %s' % (current_kml_file, str(newest_date))
	return int(newest_date)

def addChildElement(dom, parentElement, childElementName, elementText):
	"""
	Adds child element to parentElement
	"""
	
	new_child = dom.createElement(childElementName)
	parentElement.appendChild(new_child)
	
	lastChild = parentElement.lastChild # recorded in case we need to add children
	
	if elementText != "":
		new_child_text = dom.createTextNode(elementText)
		new_child.appendChild(new_child_text)

	return lastChild

def cleanFoursquareDescription(description):
	"""
	Clean up the Foursquare description
	"""
	
	# remove XML tags
	description = stripTags(description, '<description>', '</description>')
	
	# remove the leading '@'
	if description.strip().startswith("@"):
		description = description.replace("@", "", 1)

	# remove extraneous hyphen after first anchor element
	if description.find("</a>-") > -1:
		description = description.replace("</a>-", "</a>:", 1)
		
	return description
		
def appendCurrentPlacemark(current_dom, currentBaseFolder, newPlacemark):
	"""
	This recreates a placemark element and appends it to current_kml_file
	"""
	
	new_placemark_dom = current_dom.createElement("Placemark")
	currentBaseFolder.appendChild(new_placemark_dom)
	new_placemark = currentBaseFolder.lastChild	
	
	placemarkName = newPlacemark.getElementsByTagName("name")[0].firstChild.wholeText
	placemarkDescription = cleanFoursquareDescription(newPlacemark.getElementsByTagName("description")[0].toxml())
	placemarkUpdated = newPlacemark.getElementsByTagName("updated")[0].firstChild.wholeText
	placemarkPublished = newPlacemark.getElementsByTagName("published")[0].firstChild.wholeText
	pointElements = newPlacemark.getElementsByTagName("Point")
	for point in pointElements:
		placemarkCoordinates = point.getElementsByTagName("coordinates")[0].firstChild.wholeText.strip()

	# Get the actual City, State, Country for these coordinates and use that for placemarkName
	#newLatLon = placemarkCoordinates.split(',')
	#new_lon = newLatLon[0]
	#new_lat = newLatLon[1]
	#placemarkName = convertCoordsToAddress(new_lat, new_lon)
	
	
	addChildElement(current_dom, new_placemark, 'name', placemarkName)
	addChildElement(current_dom, new_placemark, 'description', placemarkDescription)
	addChildElement(current_dom, new_placemark, 'updated', placemarkUpdated)
	addChildElement(current_dom, new_placemark, 'published', placemarkPublished)
	lastChild = addChildElement(current_dom, new_placemark, 'Point', '')
	addChildElement(current_dom, lastChild, 'coordinates', placemarkCoordinates)
	
	print ">>> Appended Placemark '%s' to %r with coordinates %s" % (placemarkName, current_kml_file, placemarkCoordinates)

	# appends these placemark coordinates to the main Path element in current_kml_file
	appendCurrentPathCoordinates(current_dom, currentBaseFolder, placemarkCoordinates)

def appendCurrentPathCoordinates(current_dom, currentBaseFolder, new_coordinates):
	"""
	Appends coordinates to an existing Path in current_kml_file
	"""
	
	# loop through placemarks looking for the one that contains a name = pathPlacemarkName
	for placemark in currentBaseFolder.getElementsByTagName("Placemark"):
		isPathPlacemark = False

		for node in placemark.getElementsByTagName("name"):
			if node.tagName == "name" and stripTags(node.toxml(), '<name>', '</name>') == pathPlacemarkName:
				isPathPlacemark = True

		# loop through placemark elements looking for <LineString> element then update child <coordinates> element
		if isPathPlacemark:
			lineString = placemark.getElementsByTagName("LineString")[0] # first LineString		
			if lineString:	
				lineStringElements = lineString.getElementsByTagName("coordinates")
				if lineStringElements:
					# update <coordinates> element with new value
					for line in lineStringElements:
						if line.firstChild == None:
							coord_text = current_dom.createTextNode(new_coordinates + ",0 ")
							line.appendChild(coord_text)							
						else:
							orig_coordinates = line.firstChild.wholeText
							line.firstChild.replaceWholeText(orig_coordinates + new_coordinates + ",0 ")
						
						print ">>>> Appended coordinates '%s' to Path <LineString> in %r..." % (new_coordinates, current_kml_file)
				else:
					print ">>>> ERROR: <coordinates> missing from " + pathPlacemarkName + " <LineString> element!"
					sys.exit(0)
			else:
				print ">>>> ERROR: <LineString> missing from " + pathPlacemarkName + " element!"
				sys.exit(0)

def processFoursquarePlacemarks(current_dom, currentBaseFolder, foursquareBaseFolder, offset_date):
	"""
	Appends all Foursquare placemarks newer than offset_date to current_kml_file
	"""
	
	# go through each <Placemark> in reverse, fetch <published> date, 
	# compare to offset_date, then append to current_kml_file if newer
	foursquarePlacemarks = foursquareBaseFolder.getElementsByTagName("Placemark")
	for place in reversed(foursquarePlacemarks):
		#print ">> Fetching next Placemark from Foursquare KML..."
		#print ">> Checking the published date..."
		publishedText = place.getElementsByTagName("published")[0].firstChild.wholeText
		foursquare_date = parse(publishedText).strftime('%s')
		foursquare_date = int(foursquare_date)
		offset_date = int(offset_date)
		if foursquare_date > offset_date:
			print "\n>> Found new Foursquare Placemark ('%s')" % (place.getElementsByTagName("name")[0].firstChild.wholeText)
			updateStats('new')
			appendCurrentPlacemark(current_dom, currentBaseFolder, place)
		else:
			#print ">> Foursquare Placemark ('%s') has an older date! (%r < %r)! Skipping..." % (place.getElementsByTagName("name")[0].firstChild.wholeText, foursquare_date, offset_date)
			updateStats('skipped')

def getPlacemarksBase(kmlBase):
	"""
	Determines the layout of kmlBase and returns the base element where <Placemark>'s reside
	"""
	
	if kmlBase.getElementsByTagName("Document"):
		#print "This KML file has a <Document> element!"
		placemarksBase = kmlBase.getElementsByTagName("Document")[0]
		if placemarksBase.getElementsByTagName("Folder"):
			#print "This KML file has a <Document> with sub <Folder>! Defaulting to the first <Folder>!"
			placemarksBase = kmlBase.getElementsByTagName("Folder")[0]
	elif kmlBase.getElementsByTagName("Folder"):
		#print "This KML file DOES NOT have a <Document> element! Defaulting to the first <Folder>!"
		placemarksBase = kmlBase.getElementsByTagName("Folder")[0]
	else:
		print "> ERROR: Unable to determine layout of KML file!"
		sys.exit(0)

	return placemarksBase
	
# -----------------------------------------------------

print "> Opening " + current_kml_file
current_dom = DOM.parse(current_kml_file)
current_kml = current_dom.getElementsByTagName("kml")[0]
current_base = getPlacemarksBase(current_kml)

# -----------------------------------------------------

print "> Opening " + foursquare_kml_url
# load remote Foursquare KML
file = urllib2.urlopen(foursquare_kml_url)
data = file.read() #convert to string
file.close()
foursquare_dom = parseString(data) # parse the XML
foursquare_kml = foursquare_dom.getElementsByTagName("kml")[0]
foursquare_base = getPlacemarksBase(foursquare_kml)
	
# -------------------------------------------------------

print "\n> Determining the newest Placemark in %r..." % current_kml_file
offset_date = getNewestPublishedPlacemarkDate(current_base)

print "\n> Fetching Placemarks from Foursquare KML..."
processFoursquarePlacemarks(current_dom, current_base, foursquare_base, offset_date)

if newPlacemarks > 0:
	print "\n> Updating Current Location in %r..." % current_kml_file
	updateCurrentLocation(current_base)

print "\n> Writing new KML document to %s..." % current_kml_file
new_current_file = open(current_kml_file, "w")
current_dom.writexml(new_current_file)
new_current_file.close()

print "\n> Stats: %r new placemarks, %r skipped placemarks" % (newPlacemarks, skippedPlacemarks)

now = datetime.datetime.now()
print "\n> Finished processing on " + now.strftime("%Y-%m-%d %H:%M:%S")

#print current_dom.toprettyxml('', '')