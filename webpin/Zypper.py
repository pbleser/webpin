from webpin.PackageManager import *
from webpin.util import *
from webpin.const import *
import os

class Zypper(PackageManager):
	def __init__(self):
		PackageManager.__init__(self, 'Zypper')
		self.cmd = '/usr/bin/zypper'
		self.cache = None
		self.buildServiceRepos = None
		pass
	def _buildCacheHook(self):
		self.getCache()
		pass
	def getCache(self):
		if not self.cache:
			c = {}
			bs = {}
			try:
				zypper = os.popen('%s sl' % self.cmd, 'r')
				# skip two header lines
				zypper.readline()
				zypper.readline()
				# parse lines
				for line in zypper.readlines():
					line = line[:-1] # remove trailing \n
					# skip empty lines (not any at this point, but in order to make
					# the line parsing just a little less fragile:
					if len(line.strip()) > 0:
						fields = line.split('|')
						enabled = (fields[1].strip() == 'Yes')
						url = normalizeURL(fields[5].strip())

						m = buildServiceRegex.match(url)
						if m:
							bs[m.group(1)] = {'name': m.group(1), 'url': url, 'enabled': enabled }
							pass
						else:
							# search for matches in repoRegexMap:
							for regex, repoName in repoRegexMap.iteritems():
								if regex.search(url):
									c[repoName] = {'url': url, 'enabled': enabled }
									pass
								pass
							pass
						pass
					pass
				zypper.close()
				self.cache = c
				self.buildServiceRepos = bs
			except IOError:
				sys.stderr.write('ERROR: failed to run "%s sl"' % self.cmd)
				sys.exit(E_EXTERNAL_PROCESS)
			pass
		return self.cache
	def _hasBuildServiceChannel(self, name, buildServiceName, url):
		if self.buildServiceRepos.has_key(buildServiceName):
			data = self.buildServiceRepos[buildServiceName]
			return { 'name': data['name'],
					'disabled': not data['enabled'] }
			pass
		return None
	def _hasChannel(self, name, url):
		if self.getCache().has_key(name):
			return { 'name': name, 'disabled': not self.getCache()[name]['enabled'] }
		else:
			m = buildServiceRegex.match(url)
			if m and self.buildServiceRepos.has_key(m.group(1)):
				return { 'name': self.buildServiceRepos[m.group(1)]['name'],
						'disabled': not self.buildServiceRepos[m.group(1)]['enabled'] }
			return None
		pass
	pass

