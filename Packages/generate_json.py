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

from __future__ import print_function

import os
import sys
import atexit
import tarfile
import optparse

import supybot.world as world
unregister = [world.makeDriversDie, world.makeIrcsDie, world.startDying,
              world.finished, world.upkeep]

import plugin # I mean the Supybot plugin, the one which should be distributed
              # with this script and is runned by Supybot.

def main(filename):
    with tarfile.open(name=filename, mode='r:*') as file_:
        directory = plugin.getDirectory(file_)
        if not directory:
            print('%s is not a valid package.' % filename)
            return
        class packaging:
            """Namespace for runned code"""
            exec(file_.extractfile('%s/packaging.py' % directory).read())
        class init:
            """Namespace for runned code"""
            exec(file_.extractfile('%s/__init__.py' % directory).read())
    def getPrettyJsonFromDict(dict_):
        output = ''
        for key, value in dict_.items():
            output += """
                "%s": "%s",""" % (key, value)
        if output != '':
            output = output[0:-1] # Remove the ending comma
        return output
    output = """
        {
            "name": "%(name)s",
            "version": "%(version)s",
            "author": [
                "%(author_name)s",
                "%(author_nick)s",
                "%(author_email)s"
            ],
            "info-url": "%(info_url)s",
            "download-url": "./%(name)s-%(version)s.tar",
            "requires": {%(requires)s
            },
            "suggests": {%(suggests)s
            },
            "provides": {%(provides)s
            }
        }""" % {'name': directory,
                'version': init.__version__,
                'author_name': init.__author__.name,
                'author_nick': init.__author__.nick,
                'author_email': init.__author__.email,
                'info_url': init.__url__,
                'requires': getPrettyJsonFromDict(packaging.requires),
                'suggests': getPrettyJsonFromDict(packaging.suggests),
                'provides': getPrettyJsonFromDict(packaging.provides)}
    return output




if __name__ == '__main__':
    parser = optparse.OptionParser(usage='Usage: %prog Package.tar',
                                   version='Supybot Packager 0.1')
    (options, args) = parser.parse_args()
    if len(args) > 0:
        filename = args[0]
        output = main(filename)
    else:
        output = """
{
    "repository": {
        "maintainers": {
            "ProgVal": "progval@gmail.com"
        },
        "repo-name": "Main packages repository",
        "repo-url": "http://packages.supybot.fr.cr",
        "project-name": "Supybot-fr",
        "project-url": "http://supybot.fr.cr"
    },
    "packages": ["""
        addComma = False
        for filename in os.listdir('.'):
            if addComma:
                output += ','
            if filename.endswith('.tar'):
                output += main(filename)
            addComma = True
        output += """
    ]
}"""
    if sys.version_info > (3, 0, 0):
        # clean
        for function in unregister:
            atexit.unregister(function)
    else:
        # less clean
        for function in unregister:
            atexit._exithandlers.remove((function, (), {}))
    if output is not None:
        print(output)
