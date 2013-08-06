# Author: Pascal Bleser <pascal.bleser@opensuse.org>
# This file is licensed under the GNU General Public License version 2
# A copy of the license is available here: http://www.gnu.org/licenses/gpl-2.0.txt

import re
from webpin.layout import *

VERSION = '1.2.3'
# Software Portal URL:
server = 'webpinstant.com'
baseurl = '/ws/searchservice/Search/'
# Stable URL:
# server = 'api.opensuse-community.org'
# baseurl = '/searchservice/Search/'
globalConfigFile = '/etc/webpinrc'
defaultUserConfigFile = '~/.webpinrc'
defaultTimeout = 60
maxRedirects = 3
# default mode:
mode = 'Simple'
# used when the VERSION cannot be parsed from platform.dist()
# nor /etc/SuSE-release
defaultSuseVersion = '12.3'
# used for --latest
latestSuseVersion = defaultSuseVersion

# constants for error codes
E_SUCCESS = 0
E_NO_RESULT = 1
E_SERVER_ERROR = 2
E_NETWORK_ERROR = 3
E_QUERY_MISSING = 4
E_QUERY_TOO_MANY = 5
E_INVALID_VERSION = 6
E_CONFIG = 7
E_UNSUPPORTED_OPTION = 8
E_EXTERNAL_PROCESS = 9
E_INTERRUPTED = 10

# Map of "human-readable" names for repositories.
# The repository URLs will be matched against the regular
# expressions defined as keys in the following map, where
# the corresponding values will be used as "human-readable"
# names:
repoRegexMap = {
		re.compile(r'packman[/\.]'): 'packman',
		re.compile(r'/suser-jengelh\/'): 'jengelh',
		re.compile(r'/repo/oss/suse'): 'suse-oss',
		re.compile(r'/distribution/\d+\.\d+/repo/oss'): 'suse-oss',
		re.compile(r'/SL-\d+\.\d+/inst-source'): 'suse-oss',
		re.compile(r'/repo/non-oss/suse'): 'suse-non-oss',
		re.compile(r'/distribution/\d+\.\d+/repo/non-oss'): 'suse-non-oss',
		re.compile(r'/update/\d+'): 'suse-update',
		re.compile(r'/SL-OSS-[Ff]actory/inst-source'): 'suse-factory-oss'
		}

# flyweight for ClassicLayout:
classicLayout = ClassicLayout()

# fallbackRepoLayout is used when no match is found in repoLayout
fallbackRepoLayout = classicLayout
# override repository layouts for those that don't
# match fallbackRepoLayout:
repoLayout = {
		'suse-update': ClassicLayout('rpm')
		}

# Map of (open)SUSE versions to dist identifiers
# that must be used in the Package Search webservice URL:
distVersionMap = {
		'12.3': 'openSUSE_123',
		'12.2': 'openSUSE_122',
		'12.1': 'openSUSE_121',
		'11.4': 'openSUSE_114',
		'11.3': 'openSUSE_113',
		'11.2': 'openSUSE_112',
		'11.1': 'openSUSE_111',
		'11.0': 'openSUSE_110',
		'latest': latestSuseVersion,
		'factory': 'SUSE_Factory',
		'Factory': 'SUSE_Factory'
		}

# Specific regular expression to detect and determine
# openSUSE Build Service repositories:
buildServiceRegex = re.compile(r'.*/(?:download|software)\.opensuse\.org/(?:download|repositories)/(.+)/([^/]+)/?$')

