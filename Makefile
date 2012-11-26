all:	doc/webpin.8

VERSION := $(shell grep -E '^VERSION *= *' webpin/const.py|sed -r "s/\s+//g;s/'//g"|cut -f2 -d=)

doc/webpin.8:	./webpin.py Makefile doc/webpin.man.in webpin/const.py
	help2man --section=8 --source=openSUSE --no-info ./webpin.py \
		| cat - doc/webpin.man.in \
		| sed -e 's|(N/A)||g' \
		| sed -e 's/webpin.py/webpin/g;s/WEBPIN.PY/WEBPIN/g' > $@

.PHONY:	dist

dist:		doc/webpin.8
	/bin/rm -rf ../dist
	mkdir -p "../dist/webpin-${VERSION}"
	cp -a * "../dist/webpin-${VERSION}/"
	cd ../dist && tar --create --file=- --exclude=.svn "webpin-${VERSION}" | bzip2 -c9 > "../webpin-${VERSION}.tar.bz2"
	/bin/rm -rf ../dist
