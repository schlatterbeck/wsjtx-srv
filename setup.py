#!/usr/bin/env python
# Copyright (C) 2021-23 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ****************************************************************************

import os.path
from setuptools import setup

if os.path.exists ("VERSION"):
    with open ("VERSION", 'r', encoding="utf8") as f:
        __version__ = f.read ().strip ()
else:
    __version__ = '0+unknown'

with open ('README.rst', encoding="utf8") as f:
    description = f.read ()

license     = 'BSD License'
rq          = '>=3.7'
setup \
    ( name             = "wsjtx_srv"
    , version          = __version__
    , description      = "Library implementation of WSJTX companion program"
    , long_description = ''.join (description)
    , long_description_content_type = 'text/x-rst'
    , license          = license
    , author           = "Ralf Schlatterbeck"
    , author_email     = "rsc@runtux.com"
    , install_requires = ['rsclib', 'hamradio']
    , packages         = ['wsjtx_srv']
    , platforms        = 'Any'
    , url              = "https://github.com/schlatterbeck/wsjtx-srv"
    , entry_points     = dict
        ( console_scripts =
            [ 'wsjtx-srv=wsjtx_srv.wsjtx:main'
            , 'wbf=wsjtx_srv.wsjtx:wbf'
            ]
        )
    , python_requires  = rq
    , classifiers      = \
        [ 'Development Status :: 5 - Production/Stable'
        , 'License :: OSI Approved :: ' + license
        , 'Operating System :: OS Independent'
        , 'Topic :: Communications :: Ham Radio'
        , 'Intended Audience :: Developers'
        , 'Programming Language :: Python'
        , 'Programming Language :: Python :: 3.7'
        , 'Programming Language :: Python :: 3.8'
        , 'Programming Language :: Python :: 3.9'
        , 'Programming Language :: Python :: 3.10'
        , 'Programming Language :: Python :: 3.11'
        ]
    )
