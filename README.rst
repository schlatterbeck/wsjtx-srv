wsjtx_srv: Library for WSJTX server implementation
==================================================

:Author: Ralf Schlatterbeck <rsc@runtux.com>

This implements a simple UDP server that binds to the WSJTX UDP message
protocol port. It also provides everything for parsing and/or generating
WSJTX telegrams.

By default calling wsjtx_srv/wsjtx.py will provide a simple server that
colors all callsigns given on the command line. This should give a rough
idea of how to use this.

Changes
-------

Version 0.1: Initial implementation

- Implement serialization and deserialization of WSJTX telegrams and a
  simple server
- First Release

