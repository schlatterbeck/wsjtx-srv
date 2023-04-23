wsjtx-srv: Library for WSJT-X server implementation
===================================================

:Author: Ralf Schlatterbeck <rsc@runtux.com>

This implements a simple UDP server that binds to the WSJT-X_ UDP message
protocol port. It also provides everything for parsing and/or generating
WSJT-X_ telegrams.

By default calling ``wsjtx-srv`` will provide a simple server that
colors all callsigns not in the ADIF file for the current band. It uses
the ADIF logfile from WSJT-X_ with a default path to that file. You can
specify the correct path for your installation either via
command-line (call ``wsjtx-srv`` with the ``--help`` option) or in the
environment variable ``WBF_PATH``. It has also an implementation that
looks up DXCC-entities in my log database, but only those that have been
confirmed via LOTW.

The implementation of ``wsjtx-srv`` should give a rough idea of how to use
this in your own projects.

There is a companion-program ``wbf`` standing for *worked before* that
takes a number of callsigns on the command-line and tells you the worked
before status.

.. _WSJT-X: https://physics.princeton.edu/pulsar/k1jt/wsjtx.html

Changes
-------

Version 0.3: Small fixes

- Compatibility with older protocol versions, thanks to Sampo Savolainen
  for the patch
- Fix band lookup if no QSO on band

Version 0.2: Fix setup.py install_requires

Version 0.1: Initial implementation

- Implement serialization and deserialization of WSJT-X_ telegrams and a
  simple server
- First Release

