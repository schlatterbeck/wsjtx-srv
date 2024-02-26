# To use this Makefile, get a copy of my SF Release Tools
# git clone git://git.code.sf.net/p/sfreleasetools/code sfreleasetools
# And point the environment variable RELEASETOOL to the checkout
ifeq (,${RELEASETOOL})
    RELEASETOOL=../releasetool
endif
LASTRELEASE:=$(shell $(RELEASETOOL)/lastrelease -n)
WSJTX=wsjtx.py __init__.py
VERSIONPY=wsjtx_srv/Version.py
VERSIONTXT=VERSION
VERSION=$(VERSIONPY) $(VERSIONTXT)
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

clean:
	rm -f MANIFEST ${VERSION} notes changes default.css    \
	      README.html README.aux README.dvi README.log README.out \
	      README.tex announce_pypi
	rm -rf dist build upload upload_homepage ReleaseNotes.txt \
            ${PACKAGE}/__pycache__ wsjtx_srv.egg-info __pycache__ \
            ${CLEAN}

include $(RELEASETOOL)/Makefile-pyrelease
