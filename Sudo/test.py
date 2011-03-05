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

import supybot.ircutils as ircutils
from supybot.test import *

# Disable Admin protection against giving the 'owner' capability.
strEqual = ircutils.strEqual
def fakeStrEqual(first, second):
    if first == 'owner' and second == 'owner':
        return False
ircutils.strEqual = fakeStrEqual

class SudoTestCase(PluginTestCase):
    plugins = ('Sudo', 'User', 'Admin')

    def testAllow(self):
        self.assertNotError('register Prog Val')
        self.assertResponse('whoami', 'Prog')
        self.assertError('sudo whoami')
        self.assertNotError('capability add Prog owner')
        self.assertResponse('capabilities', '[owner]')
        self.assertError('sudo whoami')
        self.assertNotError('Sudo add spam allow foo!bar@baz whoami.*')
        self.assertResponse('whoami', 'Prog')
        self.assertResponse('sudo whoami', 'I don\'t recognize you.')
        self.assertResponse('capabilities', '[owner]')
        self.assertResponse('sudo capabilities', 'Error: Sudo not granted.')

    def testForbid(self):
        self.assertNotError('register Prog Val')
        self.assertResponse('whoami', 'Prog')
        self.assertError('sudo whoami')
        self.assertNotError('capability add Prog owner')
        self.assertResponse('capabilities', '[owner]')
        self.assertError('sudo whoami')
        self.assertNotError('Sudo add -1 spam allow foo!bar@baz .*i.*')
        self.assertResponse('sudo whoami', 'I don\'t recognize you.')
        self.assertNotError('Sudo add egg deny .*mi')
        self.assertResponse('whoami', 'Prog')
        self.assertError('sudo whoami')
        self.assertResponse('capabilities', '[owner]')
        self.assertRegexp('sudo capabilities', 'Error: '
                          'You must be registered to use this command.*')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
