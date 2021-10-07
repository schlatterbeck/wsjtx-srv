wsjtx_srv: Library for WSJTX server implementation
==================================================

:Author: Ralf Schlatterbeck <rsc@runtux.com>

This implements a simple UDP server that binds to the WSJTX_ UDP message
protocol port. It also provides everything for parsing and/or generating
WSJTX_ telegrams.

By default calling `bin/wsjtx-srv` will provide a simple server that
colors all callsigns given on the command line. It uses the ADIF logfile
from WSJTX with a default location. You can specify the correct location
for your installation either via command-line (call `wsjtx-srv` with the
`--help` option) or in the environment variable `WBF_PATH`. It has also
an implementation that looks up DXCC-entities in my log database, but
only those that have been confirmed via LOTW.
This should give a rough idea of how to use this.

Changes
-------

Version 0.1: Initial implementation

- Implement serialization and deserialization of WSJTX telegrams and a
  simple server
- First Release

