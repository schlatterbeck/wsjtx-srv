# To use this Makefile, get a copy of my SF Release Tools
# git clone git://git.code.sf.net/p/sfreleasetools/code sfreleasetools
# And point the environment variable RELEASETOOLS to the checkout
ifeq (,${RELEASETOOLS})
    RELEASETOOLS=../releasetools
endif
LASTRELEASE:=$(shell $(RELEASETOOLS)/lastrelease -n)
WSJTX=wsjtx.py __init__.py
VERSIONPY=wsjtx_srv/Version.py
VERSION=$(VERSIONPY)
README=README.rst
SRC=Makefile setup.py $(WSJTX:%.py=wsjtx_srv/%.py) \
    MANIFEST.in $(README) README.html

USERNAME=schlatterbeck
PROJECT=wsjtx_srv
PACKAGE=wsjtx_srv
CHANGES=changes
NOTES=notes

all: $(VERSION)

$(VERSION): $(SRC)

dist: all
	python setup.py sdist --formats=gztar,zip

clean:
	rm -f MANIFEST wsjtx_srv/Version.py notes changes default.css    \
	      README.html README.aux README.dvi README.log README.out \
	      README.tex announce_pypi
	rm -rf dist build upload upload_homepage ReleaseNotes.txt

include $(RELEASETOOLS)/Makefile-sf
