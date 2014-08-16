# -*- coding: utf8 -*-
###
# Copyright (c) 2013, Valentin Lorentz
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

import sys
from unittest import skip
from supybot.test import *

class CoinpanTestCase(ChannelPluginTestCase):
    plugins = ('Coinpan',)
    config = {'supybot.plugins.Coinpan.enable': True}

    def testCoinpan(self):
        self.assertSnarfNoResponse('foo')
        self.assertSnarfResponse('coin coin', 'pan pan')
        self.assertSnarfResponse('foo coin bar', 'foo pan bar')
        self.assertSnarfResponse('foo COIN bar', 'foo PAN bar')
        self.assertSnarfResponse('foo Coin bar', 'foo Pan bar')
        self.assertSnarfResponse('foo c01n bar', 'foo p4n bar')

        self.assertSnarfResponse('foo coïn bar', 'foo pän bar')
        self.assertSnarfResponse('foo cöïn bar', 'foo pän bar')
        self.assertSnarfResponse('foo côîn bar', 'foo pân bar')
        self.assertSnarfResponse('foo côïn bar', 'foo COINCOINCOINPANPANPAN bar')
        self.assertSnarfResponse('foo coiÑ bar', 'foo paÑ bar')
        self.assertSnarfResponse('foo KOIN bar', 'foo PANG bar')

        self.assertSnarfResponse('foo KOIN >o_/ bar', 'foo PANG >x_/ bar')

        self.assertSnarfResponse('foo CION bar', 'foo P∀N bar')
        self.assertSnarfResponse('foo cion bar', 'foo pɐn bar')

        self.assertSnarfResponse('foo nioc bar', 'foo nap bar')

    if sys.version_info < (2, 7, 0):
        def testCoinpan(self):
            pass
    elif sys.version_info < (3, 0, 0):
        testCoinpan = skip('Plugin not compatible with Python2.')(testCoinpan)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
