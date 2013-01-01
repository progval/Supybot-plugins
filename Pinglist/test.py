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

from supybot.test import *

prefixes = {'foo': 'foo!bar@baz',
            'qux': 'qux!quux@corge',
            'spam': 'spam!egg@test',
            'su': 'su!py@bot'}

class PinglistTestCase(ChannelPluginTestCase):
    plugins = ('Pinglist',)

    def testPing(self):
        self.prefix = prefixes['foo']
        self.assertResponse('pingall testing', 'Error: No such meeting.')
        self.assertNotError('subscribe testing')
        self.assertResponse('pingall testing', 'Ping foo')

        self.prefix = prefixes['qux']
        self.assertResponse('pingall testing', 'Ping foo')
        self.assertNotError('subscribe testing')
        self.assertRegexp('pingall testing', 'Ping (foo and qux|qux and foo)')
        self.assertResponse('pingall "something else"', 'Error: No such meeting.')
        self.assertNotError('subscribe "something else"')
        self.assertResponse('pingall "something else"', 'Ping qux')
        self.assertRegexp('pingall testing', 'Ping (foo and qux|qux and foo)')
        self.assertNotError('unsubscribe testing')
        self.assertResponse('pingall testing', 'Ping foo')
        self.assertResponse('unsubscribe testing', 'Error: You did not subscribe.')
        self.assertResponse('unsubscribe supybot', 'Error: No such meeting.')
        


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
