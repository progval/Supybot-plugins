#!/usr/bin/env python

###
# Copyright (c) 2011, Valentin Lorentz
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import os
import sys
import atexit
import tarfile
import optparse

import supybot.world as world
unregister = [world.makeDriversDie, world.makeIrcsDie, world.startDying,
              world.finished, world.upkeep]
if sys.version_info > (3, 0, 0):
    # clean
    for function in unregister:
        atexit.unregister(function)
else:
    # less clean
    for function in unregister:
        atexit._exithandlers.remove((function, (), {}))

def addToArchive(archive, path):
    for item in os.listdir(path):
        if item.startswith('.') or item.endswith('~') or \
                item.endswith('.swp') or item.endswith('.swo') or \
                item.endswith('.pyc') or item.endswith('.pyo'):
            continue
        itemPath = os.path.join(path, item)
        archive.add(itemPath, recursive=False)
        if os.path.isdir(itemPath):
            addToArchive(archive, itemPath)

def main(dirname):
    if dirname.endswith('/'):
        dirname = dirname[0:-1]
    class init:
        """Namespace for runned code"""
        exec(open('%s/__init__.py' % dirname))
    assert init.__version__ != '', 'Version is empty'
    path = '%s-%s.tar' % (dirname, init.__version__)
    try:
        os.unlink(path)
    except OSError:
        # Does not exist
        pass
    with tarfile.open(path, 'a') as archive:
        addToArchive(archive, dirname)
        names = archive.getnames()
        for name in ('__init__', 'config', 'plugin', 'test', 'packaging'):
            assert '%s/%s.py' % (dirname, name) in names, \
                    '%s.py is missing' % name

if __name__ == '__main__':
    parser = optparse.OptionParser(usage='Usage: %prog Package.tar',
                                   version='Supybot Packager 0.1')
    (options, args) = parser.parse_args()
    assert len(args) > 0
    dirname = args[0]
    output = main(dirname)
