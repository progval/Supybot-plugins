###
# Copyright (c) 2014, Valentin Lorentz
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

class PPPTestCase(PluginTestCase):
    plugins = ('PPP', 'Config')

    def testBasics(self):
        self.assertResponse('query What is the capital of Australia?',
                'Canberra')

    def testBold(self):
        self.assertResponse('triples What is the capital of Australia?',
                '(Australia, capital, \x02?\x02)')

    def testList(self):
        self.assertRegexp('query What are the capitals of the European Union?',
                '^(Brussels and Strasbourg|Strasbourg and Brussels)$')
        self.assertRegexp('query '
                'Who is the author of “Use of A Network Enabled Server System '
                'for a Sparse Linear Algebra Application”?',
                'Eddy Caron')

    def testBadApi(self):
        self.assertNotError('config plugins.PPP.api http://foo/')
        try:
            self.assertResponse('query foo',
                    'Error: Could not connect to the API.')
        finally:
            self.assertNotError('config setdefault plugins.PPP.api')

    def testHeadline(self):
        self.assertNotError('config plugins.PPP.formats.query '
                            '"$value ($headline)"')
        try:
            self.assertRegexp('query What is Brussels?',
                    '^Brussels.*The City of Brussels')
        finally:
            self.assertNotError('config setdefault plugins.PPP.formats.query')


if not network:
    class PPPTestCase(PluginTestCase):
        plugins = ('PPP',)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
