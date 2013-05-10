###
# Copyright (c) 2003-2005, James Vega
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
import time

from supybot.test import *

class DebianTestCase(PluginTestCase):
    plugins = ('Debian',)
    timeout = 100
    cleanDataDir = False
    fileDownloaded = False
    if network:
        def testDebBug(self):
            self.assertNotRegexp('debian bug 539859', r'\<em\>')
            self.assertResponse('debian bug 539859',
                                '\x02Package\x02: supybot; '
                                '\x02Subject\x02: configurable error in '
                                'ShrinkUrl; '
                                '\x02Reported\x02: by Clint Adams '
                                '<clintATdebian.org> on '
                                'Tue, 4 Aug 2009 03:39:37 +0000; '
                                '\x02Severity\x02: wishlist; '
                                '\x02Tags\x02: fixed-upstream; '
                                '<http://bugs.debian.org/cgi-bin/'
                                'bugreport.cgi?bug=539859>'.replace('AT', '@'))
            self.assertError('debian bug 551215216542')

        def testDebversion(self):
            self.assertHelp('debian version')
            self.assertRegexp('debian version lakjdfad',
                              r'^No package.*\(all\)')
            self.assertRegexp('debian version --branch unstable alkdjfad',
                r'^No package.*\(unstable\)')
            self.assertRegexp('debian version --branch stable gaim',
                              r'\d+ matches found:.*gaim.*\(stable')
            self.assertRegexp('debian version linux-wlan',
                              r'\d+ matches found:.*linux-wlan.*')
            self.assertRegexp('debian version --exact linux-wlan',
                              r'^No package.*\(all\)')
            self.assertNotError('debian version unstable')
            self.assertRegexp('debian version --branch stable unstable',
                              r'^No package.*')

        def testDebfile(self):
            self.assertHelp('debian file')
            self.assertRegexp('debian file oigrgrgregg',
                              r'^No filename.*\(stable\)')
            self.assertRegexp('debian file --branch unstable alkdjfad',
                r'^No filename.*\(unstable\)')
            self.assertResponse('debian file --exact --branch stable /bin/sh',
                    r'1 matches found: dash (stable)')
            self.assertRegexp('debian file --branch stable /bin/sh',
                              r'2 matches found:.*(?:dash.*|klibc-utils.*)')

        def testDebincoming(self):
            self.assertNotError('incoming')

        def testDebstats(self):
            self.assertNotError('stats supybot')


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
