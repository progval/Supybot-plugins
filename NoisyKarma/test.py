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

import supybot.conf as conf
from supybot.test import *

class NoisyKarmaTestCase(ChannelPluginTestCase):
    plugins = ('NoisyKarma', 'Karma')

    def setUp(self):
        super(NoisyKarmaTestCase, self).setUp()
        conf.supybot.plugins.NoisyKarma.messages.positive.get(self.channel).set('{}')
        conf.supybot.plugins.NoisyKarma.messages.negative.get(self.channel).set('{}')

    def testPositive(self):
        self.assertSnarfNoResponse('foo')
        self.assertNotError('noisykarma add 2 Interesting, %s.')
        self.assertNotError('noisykarma add 4 %s is cool!')
        self.assertSnarfNoResponse('foo')
        self.assertNoResponse('foo++')
        self.assertSnarfNoResponse('foo')
        self.assertNoResponse('foo++')
        self.assertSnarfResponse('foo', 'Interesting, foo.')
        self.assertNoResponse('foo++')
        self.assertSnarfResponse('foo', 'Interesting, foo.')
        self.assertNoResponse('foo++')
        self.assertSnarfResponse('foo', 'foo is cool!')
        self.assertNoResponse('foo++')
        self.assertSnarfResponse('foo', 'foo is cool!')
        self.assertNoResponse('foo--')
        self.assertSnarfResponse('foo', 'foo is cool!')
        self.assertNoResponse('foo--')
        self.assertSnarfResponse('foo', 'Interesting, foo.')

    def testNegative(self):
        self.assertNotError('noisykarma add -2 Eww, %s.')
        self.assertNotError('noisykarma add -4 Oh no, not %s!')
        self.assertSnarfNoResponse('bar')
        self.assertNoResponse('bar--')
        self.assertSnarfNoResponse('bar')
        self.assertNoResponse('bar--')
        self.assertSnarfResponse('bar', 'Eww, bar.')
        self.assertNoResponse('bar--')
        self.assertSnarfResponse('bar', 'Eww, bar.')
        self.assertNoResponse('bar--')
        self.assertSnarfResponse('bar', 'Oh no, not bar!')

    def testAction(self):
        self.assertNotError('noisykarma add -2 --action doesn\'t like %s.')
        self.assertSnarfNoResponse('baz')
        self.assertNoResponse('baz--')
        self.assertSnarfNoResponse('baz')
        self.assertNoResponse('baz--')
        self.assertSnarfResponse('baz', '\x01ACTION doesn\'t like baz.\x01')

    def testOverwrite(self):
        self.assertNotError('noisykarma add -2 --action doesn\'t like %s.')
        self.assertSnarfNoResponse('qux')
        self.assertNoResponse('qux--')
        self.assertSnarfNoResponse('qux')
        self.assertNoResponse('qux--')
        self.assertSnarfResponse('qux', '\x01ACTION doesn\'t like qux.\x01')
        self.assertNotError('noisykarma add -2 Eww, %s.')
        self.assertNoResponse('qux--')
        self.assertSnarfResponse('qux', 'Eww, qux.')

    def testList(self):
        self.assertNotError('noisykarma add -2 --action doesn\'t like %s.')
        self.assertNotError('noisykarma add -4 --action doesn\'t like %s.')
        self.assertNotError('noisykarma add 2 %s is nice')
        self.assertResponse('noisykarma list',
                "-4: doesn't like %s. (action: True), "
                "-2: doesn't like %s. (action: True), "
                "and 2: %s is nice (action: False)")

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
