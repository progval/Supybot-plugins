###
# Copyright (c) 2010, Valentin Lorentz
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

from supybot.test import *

class MilleBornesTestCase(PluginTestCase):
    plugins = ('MilleBornes',)
    def testInit(self):
        self.prefix = 'test!foo@bar'
        self.assertRegexp('start', 'test started.*')
        self.assertError('start')
        self.assertRegexp('drivers', '.*test.*')
        self.assertError('drive')
        self.assertResponse('abandon', 'test has left the game')
        self.assertNotRegexp('drivers', '.*test.*')
        self.assertResponse('drive', 'test is now playing!')
        self.assertRegexp('drivers', '.*test.*')
        self.prefix = 'foo!bar@baz'
        self.assertResponse('drive', 'foo is now playing!')
        self.assertRegexp('drivers', '.*test.*foo.*')
        self.assertError('drive')
        self.prefix = 'test!bar!baz'
        self.assertError('drive')
        self.prefix = 'foo!bar@baz'
        self.assertResponse('abandon', 'foo has left the game')
        self.assertRegexp('drivers', '.*test.*')
        self.assertResponse('drive', 'test is now playing!')
        self.assertRegexp('drivers', '.*foo.*test.*')
        self.prefix = 'test!bar!baz'
        self.assertResponse('abandon', 'test has left the game')
        self.assertRegexp('drivers', '.*foo.*')
        self.assertNoError('go')

    def testCheckCards(self):
        self.assertNoError('start')
        self.assertNoError('go')
        self.assertError('play 250', 'Allow cards that doesn\'t exist.')
        self.assertNoError('setcards', '50 50 50 50 50 50 50')
        self.assertError('play 100')

    def testReachGoal(self):
        self.assertNoError('start')
        self.assertNoError('go')
        self.assertNoError('setcards', '200 200 200 200 200 200 200')
        for i in range(0, 4):
            self.assertNotRegexp('play 200', '.*win.*')
        self.assertRegexp('play 200', '.*win.*')

    def testDoesntReachGoal(self):
        self.assertNoError('start')
        self.assertNoError('go')
        self.assertNoError('setcards', '200 200 200 200 200 100 50')
        for i in range(0, 3):
            self.assertNoError('play 200')
        self.assertNoError('play 100')
        self.assertError('play 200')
        self.assertError('play 50') # Has loosed the game, so he cannot play


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
