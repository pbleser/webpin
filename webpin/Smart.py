from webpin.PackageManager import *
from webpin.util import *
from webpin.const import *

import smart

#
# Additional regexes for fuzzily detecting repositories in
# smart's channel list:
#
smartChannelRegexMap = {
		'guru':
		[ re.compile(r'/guru/\d+\.\d+') ],
		'suse-oss':
		[ re.compile(r'/\d+\.\d+/repo/oss') ],
		'suse-non-oss':
		[ re.compile(r'/\d+\.\d+/repo/non-oss') ],
		'packman':
		[ re.compile(r'/packman/suse/\d+\.\d+') ],
		}

#
# And we're even going to hunt for channel names:
#
smartChannelNameMap = {
		'suse': 'suse-oss',
		'suse-oss': 'suse-oss',
		'suse-non-oss': 'suse-non-oss',
		'suse-update': 'suse-update',
		'packman': 'packman',
		'guru': 'guru',
		}

class Smart(PackageManager):
	def __init__(self):
		PackageManager.__init__(self, 'Smart')
		self.control = None
		self.invertedChannelMap = None
		self.buildServiceRepos = None
		self.names = {}
		pass
	def _buildCacheHook(self):
		self.getControl()
		if not self.invertedChannelMap:
			self.buildInvertedChannelMap()
			pass
		pass
	def _hasBuildServiceChannel(self, name, buildServiceName, url):
		if self.buildServiceRepos.has_key(buildServiceName):
			return self._buildResultFromChannelData(buildServiceName, self.buildServiceRepos[buildServiceName])
		else:
			return None
		pass
	def getControl(self):
		if not self.control:
			self.control = smart.init()
			pass
		return self.control
	def getSysConf(self):
		self.getControl()
		return smart.sysconf
	def getChannelMap(self):
		return self.getSysConf().get('channels') or {}
	def getMirrorMap(self):
		return self.getSysConf().get('mirrors') or {}
	def buildInvertedChannelMap(self):
		m = {}
		n = {}
		bs = {}
		for name, data in self.getChannelMap().iteritems():
			if data.has_key('baseurl'):
				baseurl = normalizeURL(data['baseurl'])
				m[baseurl] = name
				for url, aliases in self.getMirrorMap().iteritems():
					url = normalizeURL(url)
					if baseurl.startswith(url):
						rest = ''.join(data['baseurl'].split(url)[1:])
						while len(rest) > 0 and rest[:1] == '/':
							rest = rest[1:]
							pass
						for alias in aliases:
							aliasURL = normalizeURL(alias)
							if len(rest) > 0:
								mirrorURL = aliasURL + '/' + rest
							else:
								mirrorURL = aliasURL
								pass
							m[mirrorURL] = name
							pass
						pass
					pass
				for repoName, regexList in smartChannelRegexMap.iteritems():
					for regex in regexList:
						if regex.search(baseurl):
							n[repoName] = baseurl
							pass
						pass
					pass
				if smartChannelNameMap.has_key(name):
					n[smartChannelNameMap[name]] = baseurl
					pass
				bsm = buildServiceRegex.match(baseurl)
				if bsm:
					bs[bsm.group(1)] = data
				pass
			pass
		self.invertedChannelMap = m
		self.names = n
		self.buildServiceRepos = bs
		pass
	def _hasChannel(self, name, url):
		if self.invertedChannelMap.has_key(url):
			channelName = self.invertedChannelMap[url]
			channelData = self.getChannelMap()[channelName]
			return self._buildResultFromChannelData(channelName, channelData)
		return None
	def _fallbackChannelStrategy(self, name, url):
		if self.names.has_key(name):
			baseurl = self.names[name]
			channelName = self.invertedChannelMap[baseurl]
			channelData = self.getChannelMap()[channelName]
			return self._buildResultFromChannelData(channelName, channelData)
		return None
	def _buildResultFromChannelData(self, channelName, channelData):
		channelDisabled = channelData.has_key('disabled') and channelData['disabled']
		return { 'name': channelName, 'disabled': channelDisabled }
	pass


