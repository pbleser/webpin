# Author: Pascal Bleser <pascal.bleser@opensuse.org>
# This file is licensed under the GNU General Public License version 2
# A copy of the license is available here: http://www.gnu.org/licenses/gpl-2.0.txt

from webpin.const import *
from webpin.ColorScheme import *

from optparse import OptionParser
try:
	from ConfigParser import SafeConfigParser
except ImportError:
	from ConfigParser import ConfigParser
	pass
import sys
import os
import platform
import urllib

defaultHttpProxy = None
if os.environ.has_key('http_proxy'):
	p = os.environ['http_proxy']
	if p.startswith('http://'):
		p = urllib.splithost(urllib.splittype(p)[1])[0]
		defaultHttpProxy = p
	else:
		defaultHttpProxy = p
		pass
	pass

def configure(argv, hasRPMSupport=False, hasSmartSupport=False, hasZypperSupport=False):
	optionParser = OptionParser(
			usage="%prog [options] <searchTerm>",
			version="%%prog %s" % VERSION,
			description="A command-line client for the openSUSE Package Search web service.")
	optionParser.add_option('', '--config', action='store', type='string', dest='configFile', default=defaultUserConfigFile,
			help="user configuration file (defaults to %s)" % defaultUserConfigFile, metavar="FILE")
	optionParser.add_option('', '--skip-global-config', action='store_false', dest='readGlobalConfig', default=True,
			help="skip reading the global configuration file %s" % globalConfigFile)
	optionParser.add_option('', '--skip-config', action='store_false', dest='readConfig', default=True,
			help="skip reading configuration files alltogether")
	optionParser.add_option('-n', '--by-name', action='store_const', const='ByName', dest='mode',
			help="only search for matches in package names")
	optionParser.add_option('-c', '--by-content', action='store_const', const='ByContents', dest='mode',
			help="also search for matches in all file names")
	optionParser.add_option('-s', '--simple', action='store_const', const='Simple', dest='mode',
			help="search for matches in package names, package summaries and first match in file names (default)")
	optionParser.add_option('-d', '--dist', type='string', dest='version', default=None,
			help="openSUSE version to search for (defaults to %s, may specify 'factory' for Factory or 'latest' for latest release)" % defaultSuseVersion,
			metavar="VERSION")
	optionParser.add_option('-l', '--latest', action='store_const', const=latestSuseVersion, dest='version',
			help="search in the latest released openSUSE version (%s)" % latestSuseVersion)
	optionParser.add_option('-F', '--factory', action='store_const', const='factory', dest='version',
			help="search in the openSUSE development version (Factory)")
	optionParser.add_option('-u', '--url', action='store_true', dest='showURL', default=False,
			help="also show the URLs of the repositories that contain matching packages")
	optionParser.add_option('-a', '--arch', action='store_true', dest='showArch', default=False,
			help="also show the architectures each package match is available for (defaults to false)")
	# disabled for now, will need to add RPM release information in web service results first:
	#optionParser.add_option('-f', '--file', action='store_true', dest='showFileURL', default=False,
	#		help="also show the fully qualified RPM file URLs")
	optionParser.add_option('-t', '--timeout', action='store', type='int', dest='timeout', default=defaultTimeout,
			help="timeout in seconds for the web service request", metavar="TIMEOUT")
	optionParser.add_option('-q', '--quiet', action='store_false', dest='verbose', default=True,
			help="don't display progress information (for dumb terminals)")
	optionParser.add_option('-A', '--no-ansi', action='store_false', dest='color', default=True,
			help="don't use ANSI escape sequences (for dumb terminals), implies -q")
	optionParser.add_option('', '--theme', action='store', type='string', dest='colorScheme', default=None,
			help="color scheme to use (unless -A/--no-ansi) -- valid values: %s" % (', '.join(colorSchemeMap.keys())), metavar='NAME')
	optionParser.add_option('-D', '--dump', action='store_true', dest='dump', default=False,
			help="simply dump the XML tree sent back by the server")
	optionParser.add_option('-U', '--show-url', action='store_true', dest='showQueryURL', default=False,
			help="show the web service query URL")
	optionParser.add_option('', '--proxy', action='store', type='string', dest='proxy', default=defaultHttpProxy,
			help="HTTP proxy server to use for performing the request (if not specified, uses the http_proxy environment variable)", metavar="SERVER:PORT")
	optionParser.add_option('', '--proxy-auth', action='store', type='string', dest='proxyAuth', default=None,
			help="HTTP proxy authentication", metavar="USER:PASSWORD")
	optionParser.add_option('', '--stack-trace', action='store_true', dest='showStackTrace', default=False,
			help="show stack traces on exceptions (only useful for submitting bug reports)")
	
	helpAddonForRPM = ''
	if not hasRPMSupport:
		helpAddonForRPM = ' (N/A)'
		pass
	
	optionParser.add_option('-r', '--rpm', action='store_true', dest='rpm', default=False,
			help="compare package matches with your current RPM database" + helpAddonForRPM)
	optionParser.add_option('', '--rpm-root', action='store', type='string', dest='rpmRoot', default=None,
			help="set the root directory for the RPM database (not the path to the RPM database but the root of the system)"
			+ helpAddonForRPM,
			metavar="DIRECTORY")
	
	helpAddonForSmart = ''
	if not hasSmartSupport:
		helpAddonForSmart = ' (N/A)'
		pass
	
	optionParser.add_option('', '--smart', action='store_true', dest='smart', default=False,
			help="enable smart support to check repositories" + helpAddonForSmart)
	#optionParser.add_option('', '--smart-add', action='store_true', dest='smartAdd', default=False,
	#		help="prompt for adding repositories to smart" + helpAddonForSmart)
	
	helpAddonForZypper = ''
	if not hasZypperSupport:
		helpAddonForZypper = ' (N/A)'
	
	optionParser.add_option('', '--zypper', action='store_true', dest='zypper', default=False,
			help="enable zypper support to check repositories" + helpAddonForZypper)
	
	(options, args) = optionParser.parse_args(argv)
	
	if options.readConfig:
		try:
			from ConfigParser import SafeConfigParser
		except ImportError:
			from ConfigParser import ConfigParser
			pass
		try :
			configParser = SafeConfigParser()
		except NameError:
			configParser = ConfigParser()
			pass
	
		configModeMap = {
				'simple': 'Simple',
				'name': 'ByName',
				'content': 'ByContent'
				}
	
		userConfigFile = os.path.expanduser(options.configFile)
		configFiles = []
		if options.readGlobalConfig:
			configFiles.append(globalConfigFile)
			pass
		configFiles.append(userConfigFile)
	
		try:
			configParser.read(configFiles)
		except Exception, e:
			print >>sys.stderr, "Error while reading configuration from %s: %s" % (" and ".join(configFiles), e)
			if options.showStackTrace:
				import traceback
				traceback.print_exc()
				pass
			sys.exit(E_CONFIG)
			pass
	
		# set configuration values as defaults in OptionParser:
		def setOption(type, section, name, option=None):
			if not option:
				option = name
				pass
			if configParser.has_option(section, name):
				m = getattr(configParser, 'get%s' % type)
				optionParser.set_default(option, m(section, name))
				return True
			return False
	
		if configParser.has_option('General', 'mode'):
			modeConfig = configParser.get('General', 'mode')
			if configModeMap.has_key(modeConfig):
				optionParser.set_default('mode', configModeMap[modeConfig])
			else:
				print >>sys.stderr, 'ERROR: invalid configuration value for parameter "mode" in section "General": %s' % modeConfig
				print >>sys.stderr, 'Valid values are: %s' % ', '.join(configModeMap.keys())
				sys.exit(E_CONFIG)
				pass
			pass
		setOption('', 'General', 'distribution', 'version')
		setOption('boolean', 'Output', 'color')
		setOption('', 'Output', 'theme', 'colorScheme')
		setOption('boolean', 'Output', 'url', 'showURL')
		setOption('boolean', 'Output', 'arch', 'showArch')
		setOption('boolean', 'Output', 'verbose')
		setOption('boolean', 'Output', 'show_query_url', 'showQueryURL')
		if hasRPMSupport:
			setOption('boolean', 'RPM', 'rpm')
			setOption('', 'RPM', 'root', 'rpmRoot')
			pass
		if hasSmartSupport:
			setOption('boolean', 'Smart', 'smart')
			setOption('boolean', 'Smart', 'prompt')
			pass
		setOption('int', 'Network', 'timeout')
		setOption('', 'Network', 'proxy')
		setOption('', 'Network', 'proxy_auth', 'proxyAuth')
	
		# run option parsing again, now with defaults from the configuration files
		(options, args) = optionParser.parse_args(sys.argv)
		pass
	
	if not hasRPMSupport:
		if options.rpm:
			print >>sys.stderr, 'ERROR: you specified the --root parameter or have rpm=on in the [RPM] configuration section, but RPM support is not available.'
			print >>sys.stderr, 'SOLUTION: install the package "rpm-python" to enable RPM support.'
			sys.exit(E_UNSUPPORTED_OPTION)
			pass
		if options.rpmRoot:
			print >>sys.stderr, 'ERROR: you specified the --rpm-root parameter or have root set in the [RPM] configuration section, but RPM support is not available.'
			print >>sys.stderr, 'SOLUTION: install the package "rpm-python" to enable RPM support.'
			sys.exit(E_UNSUPPORTED_OPTION)
			pass
		pass
	if not hasSmartSupport:
		if options.smart:
			print >>sys.stderr, 'ERROR: you specified the --smart parameter or have smart=on in the [Smart] configuration section, but smart support is not available.'
			print >>sys.stderr, 'SOLUTION: install the package "smart" to enable smart support.'
			sys.exit(E_UNSUPPORTED_OPTION)
			pass
		#if options.smartAdd:
		#	sys.stderr.write('ERROR: you specified the --smart-add parameter or have add_repos=on in the [Smart] configuration section, but smart support is not available.\n')
		#	sys.stderr.write('SOLUTION: install the package "smart" to enable smart support.\n')
		#	sys.exit(E_UNSUPPORTED_OPTION)
		#	pass
		pass
	if not hasZypperSupport:
		if options.zypper:
			print >>sys.stderr, 'ERROR: you specified the --zypper parameter or have zypper=on in the [Zypper] configuration section, but zypper support is not available.'
			print >>sys.stderr, 'SOLUTION: install the package "zypper" and/or run webpin as root to enable zypper support.'
			sys.exit(E_UNSUPPORTED_OPTION)
			pass
		pass

	if not options.version:
		# Try to use the "platform" module to find out what openSUSE
		# version we're running on
		if platform.dist()[0] == "SuSE":
			options.version = platform.dist()[1]
		else:
			# Find out what openSUSE version we're running on
			# by parsing VERSION out of /etc/SuSE-release
			suseVersionRegex = re.compile(r'^VERSION\s*=\s*(.*)\s*$')
			try:
				suseReleaseFile = open('/etc/SuSE-release', 'r')
				for line in suseReleaseFile.readlines():
					m = suseVersionRegex.match(line)
					if m:
						options.version = m.group(1)
					pass
				suseReleaseFile.close()
			except IOError:
				options.version = defaultSuseVersion
				pass
			pass
		pass

	return (options, args)

