import re
import urllib

multipleDashRegex = re.compile(r'/+')

def normalizeURL(url):
	typeParts = urllib.splittype(url)
	proto = typeParts[0]
	hostParts = urllib.splithost(typeParts[1])
	host = hostParts[0]
	query = multipleDashRegex.sub('/', hostParts[1])
	if query.endswith('/'):
		query = query[:-1]
		pass
	if not query.startswith('/'):
		query = '/' + query
		pass
	normalizedURL = ''
	if proto:
		normalizedURL += proto
	else:
		normalizedURL += 'file'
		pass
	normalizedURL += '://'
	if host:
		normalizedURL += host
		pass
	normalizedURL += query
	return normalizedURL

#
# Does case-insensitive highlighting of a word in a string
#
def highlight(subject, term, color, offcolor):
	return re.compile('(%s)' % (re.escape(term)), re.I).sub('%s\g<1>%s' % (color, offcolor), subject)

#
# Little helper to fetch text nodes from DOM element nodes
#
def getChildValue(node, name):
	return node.getElementsByTagName(name).item(0).childNodes.item(0).nodeValue

