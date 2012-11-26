#!/usr/bin/python
#
# Webpin CLI client
# Command-line client for the openSUSE Package Search web service.
#
# Author: Pascal Bleser <pascal.bleser@opensuse.org>
#
# This file is licensed under the GNU General Public License version 2
# A copy of the license is available here: http://www.gnu.org/licenses/gpl-2.0.txt

from webpin.const import *
from webpin.options import *
import webpin.util
from webpin.layout import *
from webpin.ColorScheme import *

from xml.dom import minidom
import sys
import os
import platform
import signal
import re
import httplib
import urllib
import urlparse
import base64
hasRPMSupport = False
try:
	import rpm
	hasRPMSupport = True
except ImportError:
	pass
hasSmartSupport = False
try:
	from webpin.Smart import *
	hasSmartSupport = True
except ImportError:
	pass
hasZypperSupport = False
try:
	from webpin.Zypper import *
	hasZypperSupport = os.getuid() == 0 and os.path.exists('/usr/bin/zypper')
except ImportError:
	pass

(options, args) = configure(sys.argv, hasRPMSupport, hasSmartSupport, hasZypperSupport)

# whether we have more than one package backend:
multiplePackageBackends = options.smart and options.zypper

options.showFileURL = False # disabled for now
timeout = options.timeout
verbose = options.verbose
ts = None # RPM transaction object singleton, initialized in ResultTree.show()
color = options.color
if not color:
	verbose = False
	pass
version = options.version

# validate the version
versionFields = version.split('.')
if len(versionFields) == 2:
	if int(versionFields[0]) < 10 or (int(versionFields[0]) == 10 and int(versionFields[0]) < 3):
		# < 10.3 is not indexed by the Package Search service, use 10.3 instead
		# (nearest match)
		version = '10.3'
		pass
	pass

if options.mode != None:
	mode = options.mode
	pass

# Validate the query parameter
if len(args) < 2:
	print "ERROR: you must specify the search criteria as a parameter"
	sys.exit(E_QUERY_MISSING)
	pass
if len(args) > 2:
	print "ERROR: you may only specify one search criteria as a parameter"
	sys.exit(E_QUERY_TOO_MANY)
	pass
query = args[1]

# determine the dist identifier to pass in the webservice URL
if distVersionMap.has_key(version):
	dist = distVersionMap[version]
else:
	print "ERROR: invalid or unsupported value for distribution version: \"%s\"" % version
	print "Valid values are: %s" % ', '.join(distVersionMap.keys())
	sys.exit(E_INVALID_VERSION)
	pass
#
# Set ANSI escape sequence constants,
# depending on the color option
#
if not color:
	cs = NoColorScheme()
else:
	cs = colorSchemeMap['default']
	if options.colorScheme and colorSchemeMap.has_key(options.colorScheme):
		cs = colorSchemeMap[options.colorScheme]
		pass
	pass

#
# Helper function for in-place logging
#
def log(message):
	if verbose:
		sys.stdout.write("\033[0G\033[K\033[37m... %s\033[0m" % (message))
		sys.stdout.flush()
		pass
	pass

def clearLog():
	if verbose:
		sys.stdout.write("\033[0G\033[K")
		sys.stdout.flush()
		pass
	pass

#
# Global smart instance (initialized if supported and when needed)
#
if hasSmartSupport:
	smartSingleton = Smart()
else:
	smartSingleton = None
	pass

#
# Global zypper instance (initialized if supported and when needed)
#
if hasZypperSupport:
	zypperSingleton = Zypper()
else:
	zypperSingleton = None
	pass

#
# Simple, dumb data holder classes for package search results:
#
class PackageResult:
	def __init__(self, name, version, repoURL, repoName, archs, summary, matchedFileNames):
		self.name = name
		self.version = version
		self.repoURL = repoURL
		self.repoName = repoName
		self.archs = archs
		self.summary = summary
		self.matchedFileNames = matchedFileNames
		pass
	pass

class Result:
	def __init__(self, parentTree, name, summary):
		self.parent = parentTree
		self.name = name
		self.summary = summary
		self.packages = []
		self.versions = []
		self.versionRepoNames = {}
		self.repoNames = []
		self.repoURLs = {}
		self.files = []
		self.fileRepoNames = {}
		self.versionArchs = {}
		self.versionRepoArchs = {}
		pass
	def add(self, package):
		if not package.version in self.versions:
			self.packages.append(package)
			self.versions.append(package.version)
			self.versionRepoNames[package.version] = []
			self.versionArchs[package.version] = []
			self.versionRepoArchs[package.version] = {}
			pass
		if not package.repoName in self.versionRepoNames[package.version]:
			self.versionRepoNames[package.version].append(package.repoName)
			pass
		if not package.repoName in self.versionRepoArchs[package.version]:
			self.versionRepoArchs[package.version][package.repoName] = package.archs
			self.versionRepoArchs[package.version][package.repoName].sort()
			pass
		if not package.repoName in self.repoNames:
			self.repoNames.append(package.repoName)
			self.repoURLs[package.repoName] = package.repoURL
			pass
		for file in package.matchedFileNames:
			if file in self.files:
				self.fileRepoNames[file].append(package.repoName)
			else:
				self.files.append(file)
				self.fileRepoNames[file] = [package.repoName]
				pass
			pass
		for arch in package.archs:
			if not arch in self.versionArchs[package.version]:
				self.versionArchs[package.version].append(arch)
				pass
			pass
		pass
	def hasPerRepositoryArch(self, version):
		for repoName in self.versionRepoNames[version]:
			self.versionArchs[version].sort() # mmh, where's the SortedList..
			if self.versionArchs[version] != self.versionRepoArchs[version][repoName]:
				return True
			pass
		return False
	def show(self):
		global ts
		print "* %s%s%s: %s" % (cs.packageName, highlight(self.name, self.parent.query, cs.queryHighlight,
			cs.reset + cs.packageName),
			cs.reset, highlight(self.summary, self.parent.query))
		rpmDBMatchVersion = None
		if ts != None:
			m = ts.dbMatch("name", str(self.name))
			rpmDBMatches = []
			for hdr in m:
				if (not rpmDBMatchVersion) or (rpm.labelCompare(('0', hdr['version'], '0'), ('0', rpmDBMatchVersion, '0')) > 0):
					rpmDBMatchVersion = hdr['version']
					pass
				rpmDBMatches.append('%s-%s-%s [%s]' % (hdr['name'], hdr['version'], hdr['release'], hdr['arch']))
				pass
			if len(rpmDBMatches) > 0:
				print "   %sinstalled: %s%s" % (cs.installed, ' '.join(rpmDBMatches), cs.reset)
			else:
				print "   %s(not installed)%s" % (cs.notInstalled, cs.reset)
				pass
			pass
		for package in self.packages:
			if options.showArch:
				showArchPerRepo = self.hasPerRepositoryArch(package.version)
			else:
				showArchPerRepo = False
				pass
			if showArchPerRepo:
				sys.stdout.write("   - %s %s" % (
					package.version,
					formatReposWithArch(self.versionRepoNames[package.version], self.versionRepoArchs[package.version])
					))
			else:
				sys.stdout.write("   - %s %s" % (
					package.version,
					formatRepos(self.versionRepoNames[package.version], self.repoURLs)
					))
				if options.showArch:
					sys.stdout.write(' ')
					sys.stdout.write(formatArchs(self.versionArchs[package.version]))
					pass
				pass
			if rpmDBMatchVersion:
				cmpRc = rpm.labelCompare(('0', rpmDBMatchVersion, '0'), ('0', package.version, '0'))
				if cmpRc == 0:
					cmpLabel = 'SAME'
				elif cmpRc < 0:
					cmpLabel = 'NEWER'
				else:
					cmpLabel = 'OLDER'
					pass
				sys.stdout.write(' %s(%s)%s' % (cs.rpmStatus, cmpLabel, cs.reset))
				pass
			print
			if options.showFileURL:
				for repoName in self.versionRepoNames[package.version]:
					layout = fallbackRepoLayout
					if repoLayout.has_key(repoName):
						layout = repoLayout[repoName]
						pass
					for arch in self.versionArchs[package.version]:
						print "     @ %s" % layout.binary(
								self.repoURLs[repoName],
								'%s-%s.%s.rpm' % (package.name, package.version, arch),
								arch)
						pass
					pass
				pass
			if options.showURL:
				for repoName in self.versionRepoNames[package.version]:
 					url = self.repoURLs[repoName]
 					m = buildServiceRegex.search(url)
 					if m:
  						project = m.group(1).replace('/', '')
  						repoFileUrl = '%s/%s.repo' % (url, project)
  						url = repoFileUrl
  						pass
					print "     @ %s" % formatRepoURL(url)
				pass
			for filename in self.files:
				print "     %s%s" % (cs.filePrefix, highlight(filename, query, cs.fileHighlight))
				pass
			pass
		pass
	pass

class ResultTree:
	def __init__(self, dist, query):
		global smartSingleton
		global zypperSingleton
		self.dist = dist
		self.query = query
		self.resultOrder = []
		self.results = {}
		self.hits = 0
		self.repoMap = {}
		self.smart = smartSingleton
		self.zypper = zypperSingleton
		pass
	def add(self, package):
		self.hits += 1
		if not self.results.has_key(package.name):
			self.results[package.name] = Result(self, package.name, package.summary)
			pass
		self.results[package.name].add(package)
		if not package.name in self.resultOrder:
			self.resultOrder.append(package.name)
			pass
		self.repoMap[package.repoName] = package.repoURL
		pass
	def show(self):
		global ts
		print "%s%d results (%d packages) found for \"%s%s%s\" in %s%s" % (
				cs.headerStart, self.hits, len(self.results),
				cs.queryHighlight, self.query, cs.headerAfterQueryHighlight,
				self.dist, cs.headerEnd)
		if options.rpm:
			if options.rpmRoot:
				ts = rpm.ts(options.rpmRoot)
			else:
				ts = rpm.ts()
				pass
			ts.setVSFlags(rpm.RPMVSF_NORSA | rpm.RPMVSF_NODSA) # speeds up query
			pass
		for name in self.resultOrder:
			r = self.results[name]
			r.show()
			pass
		pass
	pass

def highlight(subject, term, color=cs.queryHighlight, offcolor=cs.reset):
	return webpin.util.highlight(subject, term, color, offcolor)

#
# Helper to format repositories and such with nifty colours
#
def decorateRepos(repos, urlMap):
	global smartSingleton
	global zypperSingleton
	if urlMap:
		results = []
		for name in repos:
			result = name
			if urlMap.has_key(name):
				url = urlMap[name]
				if hasSmartSupport and options.smart and smartSingleton:
					state = smartSingleton.hasChannel(name, url)
					if not state:
						result += cs.smartRepoNo
					elif state['disabled']:
						result += cs.smartRepoDisabled
					else:
						result += cs.smartRepoYes
						pass
					pass
				if hasZypperSupport and options.zypper and zypperSingleton:
					state = zypperSingleton.hasChannel(name, url)
					if not state:
						result += cs.zypperRepoNo
					elif state['disabled']:
						result += cs.zypperRepoDisabled
					else:
						result += cs.zypperRepoYes
						pass
					pass
				pass
			results.append(result)
			pass
		return results
	else:
		return repos
	pass

def formatRepos(repos, urlMap=None):
	return "%s[%s%s%s]%s" % (cs.repoSeparator, cs.repoName,
			('%s | %s' % (cs.repoSeparator, cs.repoName)).join(decorateRepos(repos, urlMap)),
			cs.repoSeparator, cs.reset)
def formatReposWithArch(repos, archMap):
	repoItems = []
	for repo in repos:
		repoItems.append("%s%s" % (repo, formatArchs(archMap[repo])))
		pass
	return formatRepos(repoItems)

def formatRepoURL(url):
	return "%s%s%s" % (cs.repoURL, url, cs.reset)
def formatArchs(archs):
	return "%s{%s%s%s}%s" % (cs.archSeparator, cs.arch,
			('%s,%s' % (cs.archSeparator, cs.arch)).join(archs),
			cs.archSeparator, cs.reset)

#
# Parses a <package/> element and create a PackageResult object
#
def parsePackage(node):
	name = getChildValue(node, 'name')
	version = getChildValue(node, 'version')
	summary = getChildValue(node, 'summary')
	repoURL = getChildValue(node, 'repoURL')
	repo = repoURL
	niceRepoName = None
	for r, repoName in repoRegexMap.iteritems():
		if r.search(repoURL):
			niceRepoName = repoName
			break
		pass
	if niceRepoName == None:
		m = buildServiceRegex.match(repoURL)
		if m:
			niceRepoName = m.group(1)
			pass
		pass
	if niceRepoName != None:
		repo = niceRepoName
		pass
	archs = []
	archsNode = node.getElementsByTagName('archs').item(0)
	if archsNode:
		for archNode in archsNode.getElementsByTagName('arch'):
			archs.append(archNode.childNodes.item(0).nodeValue)
			pass
		pass
	fileMatches = []
	for matchedFileNameNode in node.getElementsByTagName('matchedFileName'):
		fileMatches.append(matchedFileNameNode.childNodes.item(0).nodeValue.strip())
		pass
	return PackageResult(name, version, repoURL, repo, archs, summary, fileMatches)

# The URL to use to invoke the Package Search web service:
url = baseurl + "%s/%s/%s" % (mode, dist, urllib.quote(query))
#print "url: %s" % url

def connectionTimeoutHandler(signum, frame):
	raise IOError, 'connection timed out after %d seconds' % timeout

def fetch(server, url):
	# Connect to the Package Search web service
	try:
		if options.proxy:
			h = httplib.HTTPConnection(options.proxy)
		else:
			h = httplib.HTTPConnection(server)
			pass
		pass
	except Exception, e:
		clearLog()
		print >>sys.stderr, "ERROR: caught exception while building HTTPConnection: %s" % e
		if options.showStackTrace:
			import traceback
			traceback.print_exc()
			pass
		sys.exit(E_NETWORK_ERROR)
		pass

	try:
		log("performing request on http://%s%s" % (server, url))
		h.connect()
		if options.proxy:
			h.putrequest('GET', 'http://%s%s' % (server, url))
		else:
			h.putrequest('GET', url)
		h.putheader('User-Agent', 'webpin/%s' % VERSION)
		if options.proxyAuth:
			h.putheader('Proxy-Authorization', "Basic " + base64.encodestring(options.proxyAuth))
		h.putheader('Accept', 'text/xml')
		h.putheader('Accept', 'text/html')
		h.putheader('Accept', 'text/plain')
		h.endheaders()
		return h.getresponse(), h
	except Exception, e:
		clearLog()
		print >>sys.stderr, "ERROR: caught exception while connecting and sending request to server: %s" % e
		if options.showStackTrace:
			import traceback
			traceback.print_exc()
			pass
		sys.exit(E_NETWORK_ERROR)
		pass
	pass

signal.signal(signal.SIGALRM, connectionTimeoutHandler)
signal.alarm(timeout)
redirects = 0
try:
	r, h = fetch(server, url)
	while (r.status >= 300 and r.status <= 399) and redirects < maxRedirects:
		signal.alarm(timeout) # reset timeout counter to initial timeout value
		redirects += 1
		r.close()
		h.close()
		redirectURL = r.getheader('location')
		log("redirected to %s" % redirectURL)
		if options.showQueryURL:
			clearLog()
			print "Redirected to query URL: %s" % redirectURL
			print
			pass
		host, path = urlparse.urlparse(redirectURL)[1:3]
		r, h = fetch(host, path)
		pass
	if redirects >= maxRedirects:
		clearLog()
		print >>sys.stderr, "ERROR: failed to send request to server, too many redirects (%d)" % redirects
		sys.exit(E_NETWORK_ERROR)
		pass
except KeyboardInterrupt:
    print >>sys.stderr
    print >>sys.stderr, "Interrupted by user"
    sys.exit(E_INTERRUPTED)

finally:
	# indeed, this try..finally construct isn't exactly straightforward
	# but needed for backwards compatibility:
	# http://docs.python.org/ref/try.html
	signal.alarm(0)
	pass

rc = E_SUCCESS	# will be used to store the system exit code

if r.status == 200:
	log("reading response data")
	data = r.read()
	r.close()
	h.close()

	if options.dump:
		clearLog()
		if options.showQueryURL:
			print "Query URL: http://%s%s" % (server, url)
			print
			pass
		print data
		sys.exit(rc)
		pass

	log("parsing XML")
	doc = minidom.parseString(data)
	log("processing results DOM tree")
	packagesNode = doc.getElementsByTagNameNS("http://datastructures.pkgsearch.benjiweber.co.uk", "packages").item(0)

	t = ResultTree(dist, query)

	for packageNode in packagesNode.getElementsByTagName("package"):
		package = parsePackage(packageNode)
		t.add(package)
		pass

	clearLog()

	if options.showQueryURL:
		print "Query URL: http://%s%s" % (server, url)
		pass

	if t.hits > 0:
		t.show()
	else:
		print "No results found for \"%s\" in %s" % (query, dist)
		rc = E_NO_RESULT
		pass
else:
	r.close()
	h.close()
	clearLog()
	print >>sys.stderr, "FAILED: received error from server: %s %s" % (r.status, r.reason)
	rc = E_SERVER_ERROR
	pass

sys.exit(rc)

