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

from supybot.test import *

class VariablesTestCase(ChannelPluginTestCase):
    plugins = ('Variables',)

    def testSetGet(self):
        self.assertError('get foo')
        self.assertNotError('set foo bar')
        self.assertResponse('get foo', 'bar')
        self.assertNotError('set foo baz')
        self.assertResponse('get foo', 'baz')

    def testChannel(self):
        self.assertError('get --domain channel foo')
        self.assertError('get --domain channel --name #test foo')
        self.assertError('get --domain channel --name #egg foo')
        self.assertError('get foo')
        self.assertNotError('set --domain channel foo bar')
        self.assertResponse('get --domain channel foo', 'bar')
        self.assertResponse('get --domain channel --name #test foo', 'bar')
        self.assertError('get --domain channel --name #egg foo')
        self.assertError('get foo')

    def testNetwork(self):
        self.assertError('get --domain network foo')
        self.assertError('get --domain network --name test foo')
        self.assertError('get --domain network --name foonet foo')
        self.assertError('get foo')
        self.assertNotError('set --domain network foo bar')
        self.assertResponse('get --domain network foo', 'bar')
        self.assertResponse('get --domain network --name test foo', 'bar')
        self.assertError('get --domain network --name foonet foo')
        self.assertError('get foo')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
