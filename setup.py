#!/usr/bin/env python
# Copyright (C) 2021 Dr. Ralf Schlatterbeck Open Source Consulting.
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

try :
    from wsjtx_srv.Version import VERSION
except :
    VERSION = None
from warnings       import filterwarnings
from distutils.core import setup, Extension

filterwarnings \
    ( "ignore"
    , "Unknown distribution option: 'install_requires'"
    )

description = []
with open ('README.rst') as f :
    for line in f :
        description.append (line)

license     = 'BSD License'
rq          = '>=3.7'
setup \
    ( name             = "wsjtx_srv"
    , version          = VERSION
    , description      = "Library implementation of WSJTX companion program"
    , long_description = ''.join (description)
    , license          = license
    , author           = "Ralf Schlatterbeck"
    , author_email     = "rsc@runtux.com"
    , install_requires = ['rsclib', 'hamradio']
    , packages         = ['wsjtx_srv']
    , platforms        = 'Any'
    , url              = "https://github.com/schlatterbeck/wsjtx-srv"
    , scripts          = ['bin/wsjtx-srv', 'bin/wbf']
    , python_requires  = rq
    , classifiers      = \
        [ 'Development Status :: 5 - Production/Stable'
        , 'License :: OSI Approved :: ' + license
        , 'Operating System :: OS Independent'
        , 'Programming Language :: Python'
        , 'Intended Audience :: Developers'
        , 'Programming Language :: Python :: 3.7'
        , 'Programming Language :: Python :: 3.8'
        , 'Programming Language :: Python :: 3.9'
        ]
    )
