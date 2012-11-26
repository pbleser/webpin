#
# Base class for repository layout strategies, to
# infer file locations from repository URLs.
#
class RepositoryLayout:
	def __init__(self):
		pass
	def binary(self, baseurl, filename, arch):
		raise Exception, 'undefined'
	def source(self, baseurl, filename):
		return Exception, 'undefined'
	pass

#
# Classic implementation, optionally with a prefix.
#
class ClassicLayout(RepositoryLayout):
	def __init__(self, prefix=''):
		if len(prefix) > 0:
			self.prefix = prefix + '/'
		else:
			self.prefix = prefix
		pass
	def binary(self, baseurl, filename, arch):
		return '%s/%s%s/%s' % (baseurl, self.prefix, arch, filename)
	def source(self, baseurl, filename):
		return '%s/%ssrc/%s' % (baseurl, self.prefix, filename)
	pass


