# Author: Pascal Bleser <pascal.bleser@opensuse.org>
# This file is licensed under the GNU General Public License version 2
# A copy of the license is available here: http://www.gnu.org/licenses/gpl-2.0.txt

from webpin.util import *
from webpin.const import *

class PackageManager:
	def __init__(self, name):
		self.name = name
		pass
	def _buildCacheHook(self):
		pass
	def _hasBuildServiceChannel(self, name, buildServiceName, url):
		pass
	def _hasChannel(self, name, url):
		pass
	def _fallbackChannelStrategy(self, name, url):
		return None
	def hasChannel(self, name, url):
		url = normalizeURL(url)

		self._buildCacheHook()

		result = None

		#
		# Special handling for some repositories here...
		# (ugly, will find a more pluggable/clean way later)
		#
		m = buildServiceRegex.match(url)
		if m:
			result = self._hasBuildServiceChannel(name, m.group(1), url)
		elif name == "guru":
			# check for yast2 and rpm-md repository matches
			result = self._hasChannel(name, url)
			if not result:
				if url.endswith('/RPMS'):
					# tried the RPM-MD URL, now try the YaST2 repo URL:
					return self._hasChannel(name, url[:-5])
				else:
					# tried the YaST2 repo URL, now try the RPM-MD one:
					return self._hasChannel(name, url + '/RPMS')
				pass
			pass
		elif url.endswith('/suse'):
			result = self._hasChannel(name, url)
			if not result:
				result = self._hasChannel(name, url[:-5])
				pass
			pass
		elif url.endswith('/inst-source'):
			result = self._hasChannel(name, url)
			if not result:
				result = self._hasChannel(name, url + '/suse')
				pass
			pass
		else:
			result = self._hasChannel(name, url)
			pass

		# fallback strategies, let's try some fuzzy logic (sort of):
		if not result:
			result = self._fallbackChannelStrategy(name, url)
			pass

		return result
	pass
	
