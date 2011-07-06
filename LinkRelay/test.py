###
# Copyright (c) 2010, quantumlemur
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

class LinkRelayTestCase(ChannelPluginTestCase):
    plugins = ('LinkRelay','Config', 'User')

    def testAdd(self):
        self.assertNotError('config supybot.plugins.LinkRelay.relays ""')
        self.assertNotError('linkrelay add --from #foo@bar --to #baz@bam')
        self.assertResponse('config supybot.plugins.LinkRelay.relays',
                            '#foo | bar | #baz | bam | ')

        self.assertNotError('config supybot.plugins.LinkRelay.relays ""')
        self.assertNotError('linkrelay add --from #foo@bar --to #baz@bam '
                            '--reciprocal')
        self.assertResponse('config supybot.plugins.LinkRelay.relays',
                            '#foo | bar | #baz | bam |  || '
                            '#baz | bam | #foo | bar | ')

        self.assertNotError('config supybot.plugins.LinkRelay.relays ""')
        self.assertNotError('linkrelay add --from #foo@bar')
        self.assertResponse('config supybot.plugins.LinkRelay.relays',
                            '#foo | bar | #test | test | ')

        self.assertNotError('config supybot.plugins.LinkRelay.relays ""')
        self.assertNotError('linkrelay add --to #foo@bar')
        self.assertResponse('config supybot.plugins.LinkRelay.relays',
                            '#test | test | #foo | bar | ')

    def testRemove(self):
        self.assertNotError('config supybot.plugins.LinkRelay.relays '
                            '"#foo | bar | #baz | bam | "')
        self.assertNotError('linkrelay remove --from #foo@bar --to #baz@bam')
        self.assertResponse('config supybot.plugins.LinkRelay.relays', ' ')

    def testSubstitute(self):
        self.assertNotError('config supybot.plugins.LinkRelay.substitutes ""')
        self.assertNotError('linkrelay substitute foobar foo*bar')
        self.assertResponse('config supybot.plugins.LinkRelay.substitutes',
                            'foobar | foo*bar')
        self.assertNotError('linkrelay substitute baz b*z')
        self.assertResponse('config supybot.plugins.LinkRelay.substitutes',
                            'foobar | foo*bar || baz | b*z')

    def testNoSubstitute(self):
        self.assertNotError('config supybot.plugins.LinkRelay.substitutes '
                            'foobar | foo*bar || baz | b*z')
        self.assertNotError('linkrelay nosubstitute baz')
        self.assertResponse('config supybot.plugins.LinkRelay.substitutes',
                            'foobar | foo*bar')
        self.assertNotError('linkrelay nosubstitute foobar')
        self.assertResponse('config supybot.plugins.LinkRelay.substitutes', ' ')



# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

