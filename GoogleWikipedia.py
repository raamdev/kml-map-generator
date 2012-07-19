import sys # Used to add the BeautifulSoup folder the import path
import urllib2 # Used to read the html document
import urllib # Used to urlencode search data

def getGoogleWikipediaArticleURL(search_term = ""):
	"""
	Returns the URL to the first Wikipedia article returned by 
	a Google search result for search_term
	"""
	
	# Only search Wikipedia.org
	search_term = "site:wikipedia.org " + search_term
	
	# Build search query string and urlencode
	query = { 'q' : search_term}
	search_engine_url = "http://google.com/search?num=1&"
	search_url = search_engine_url + urllib.urlencode(query)

	# Use BeautifulSoup to search Google and get results
	# Sourced from http://stackoverflow.com/a/4372167/130664
	
	### Import Beautiful Soup
	### Here, I have the BeautifulSoup folder in the level of this Python script
	### So I need to tell Python where to look.
	sys.path.append("./BeautifulSoup")
	from BeautifulSoup import BeautifulSoup

	### Create opener with Google-friendly user agent
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]

	### Open page & generate soup
	url = search_url
	page = opener.open(url)
	soup = BeautifulSoup(page)

	### Parse and find
	### Looks like google contains URLs in <cite> tags.
	### Since we only want the first result, grab it and return its contents (url)
	return "http://" + soup.findAll('cite')[0].text
