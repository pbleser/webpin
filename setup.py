#!/usr/bin/env python
from distutils.command.install_data import install_data
from distutils.sysconfig import get_python_lib
from distutils.core import setup, Extension
from distutils.dep_util import newer
from distutils.log import info
from distutils import sysconfig
import distutils.file_util
import distutils.dir_util
import sys, os
import glob
import re

verpat = re.compile(r"^VERSION *= *\'(.*)\'")
for data in open("webpin/const.py").readlines():
	m = verpat.search(data)
	if m:
		VERSION = m.group(1)
		break
	pass
if not m:
	sys.exit("error: can't find VERSION")
	pass

# Make distutils copy smart.py to smart.
copy_file_orig = distutils.file_util.copy_file
copy_tree_orig = distutils.dir_util.copy_tree
def copy_file(src, dst, *args, **kwargs):
    if dst.endswith("bin/webpin.py"):
        dst = dst[:-3]
    return copy_file_orig(src, dst, *args, **kwargs)
def copy_tree(*args, **kwargs):
    outputs = copy_tree_orig(*args, **kwargs)
    for i in range(len(outputs)):
        if outputs[i].endswith("bin/webpin.py"):
            outputs[i] = outputs[i][:-3]
    return outputs
distutils.file_util.copy_file = copy_file
distutils.dir_util.copy_tree = copy_tree

PYTHONLIB = os.path.join(get_python_lib(standard_lib=1, prefix=""),
                         "site-packages")

config_h = sysconfig.get_config_h_filename()
config_h_vars = sysconfig.parse_config_h(open(config_h))

packages = [ "webpin" ]
                    
setup(name="webpin",
      version = VERSION,
      description = "Command-line tool to query the openSUSE Package Search web service",
      author = "Pascal Bleser",
      author_email = "pascal.bleser@opensuse.org",
      license = "GPL2",
      long_description =
"""\
Webpin is a command-line tool to query the openSUSE Package Search web service.
""",
      packages = packages,
      scripts = ["webpin.py"],
      data_files = [
                    ("share/man/man5/", glob.glob("doc/*.5")),
                    ("share/man/man8/", glob.glob("doc/*.8")),
                    ("/etc/", ["config/webpinrc"]),
                   ],
      )

