class ColorScheme:
	def __init__(self):
		pass
	pass

class LightColorScheme(ColorScheme):
	def __init__(self):
		ColorScheme.__init__(self)
		self.reset = '\033[0m'
		self.headerAfterQueryHighlight = '\033[44;33;1m'
		self.headerStart = self.reset + self.headerAfterQueryHighlight + '   '
		self.queryHighlight = '\033[31;1m'
		self.headerEnd = '\033[K\033[0m'
		self.repoName = '\033[32m'
		self.repoSeparator = '\033[37m'
		self.repoURL = '\033[34;4m'
		self.packageName = '\033[4m'
		self.filePrefix = '\033[34m>>' + self.reset + ' '
		self.fileHighlight = '\033[34m'
		self.arch = '\033[35m'
		self.archSeparator = self.repoSeparator
		self.installed = '\033[34m'
		self.notInstalled = '\033[37m'
		self.rpmStatus = self.installed
		self.smartRepoYes = '\033[32m(S:y)' + self.reset
		self.smartRepoNo = '\033[31m(S:n)' + self.reset
		self.smartRepoDisabled = '\033[33m(S:d)' + self.reset
		self.zypperRepoYes = '\033[32m(Z:y)' + self.reset
		self.zypperRepoNo = '\033[31m(Z:n)' + self.reset
		self.zypperRepoDisabled = '\033[33m(Z:d)' + self.reset
		pass
	pass

class DarkColorScheme(LightColorScheme):
	def __init__(self):
		LightColorScheme.__init__(self)
		self.filePrefix = '\033[34;1m>>' + self.reset + ' '
		self.fileHighlight = '\033[36;1m'
		self.installed = '\033[36;1m'
		self.repoURL = '\033[36;4;1m'
		self.arch = '\033[35;1m'
		self.repoName = '\033[32;1m'
		self.repoSeparator = '\033[0;37m'
		self.smartRepoYes = '\033[32;1m(S:y)' + self.reset
		self.zypperRepoYes = '\033[32;1m(Z:y)' + self.reset
		self.smartRepoDisabled = '\033[33;1m(S:d)' + self.reset
		self.zypperRepoDisabled = '\033[33;1m(Z:d)' + self.reset
		pass
	pass

class NoColorScheme(ColorScheme):
	def __init__(self):
		ColorScheme.__init__(self)
		self.reset = \
		self.headerAfterQueryHighlight = \
		self.headerStart = \
		self.queryHighlight = \
		self.repoName = \
		self.repoSeparator = \
		self.repoURL = \
		self.packageName = \
		self.fileHighlight = \
		self.arch = \
		self.archSeparator = \
		self.installed = \
		self.notInstalled = \
		self.rpmStatus = \
		''
		self.headerEnd = '\n'
		self.filePrefix = '>> '
		self.smartRepoYes = '(S:y)'
		self.smartRepoNo = '(S:n)'
		self.smartRepoDisabled = '(S:d)'
		self.zypperRepoYes = '(Z:y)'
		self.zypperRepoNo = '(Z:n)'
		self.zypperRepoDisabled = '(Z:d)'
		pass
	pass

colorSchemeMap = {
		'default': LightColorScheme(),
		'light': LightColorScheme(),
		'dark': DarkColorScheme(),
		'none': NoColorScheme(),
		}



