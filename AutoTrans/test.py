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
import supybot.conf as conf

class AutoTransTestCase(ChannelPluginTestCase):
    plugins = ('AutoTrans', 'Google')

    if network:
        def testTranslate(self):
            def feedMsg(msg):
                return self._feedMsg(msg, usePrefixChar=False)
            self.assertNotError('config channel plugins.AutoTrans.queries '
                    'foo:en bar:de')
            while self.irc.takeMsg():
                pass
            m = feedMsg('This is a test')
            self.assertEqual(m.command, 'NOTICE', m)
            self.assertEqual(m.args[0], 'bar', m)
            self.assertEqual(m.args[1], '<test@#test> Das ist ein Test', m)

            self.assertEqual(self.irc.takeMsg(), None)

            m = feedMsg('Dies ist ein Test')
            self.assertEqual(m.command, 'NOTICE', m)
            self.assertEqual(m.args[0], 'foo', m)
            self.assertEqual(m.args[1], '<test@#test> This is a test', m)

            self.assertEqual(self.irc.takeMsg(), None)

            msgs = set((feedMsg('Ceci est un test'), self.irc.takeMsg()))
            msgs_foo = list(filter(lambda m:m.args[0]=='foo', msgs))
            msgs_bar = list(filter(lambda m:m.args[0]=='bar', msgs))
            self.assertEqual(len(msgs_foo), 1)
            self.assertEqual(len(msgs_bar), 1)
            m = msgs_foo[0]
            self.assertEqual(m.command, 'NOTICE', m)
            self.assertEqual(m.args[0], 'foo', m)
            self.assertEqual(m.args[1], '<test@#test> This is a test', m)
            m = msgs_bar[0]
            self.assertEqual(m.command, 'NOTICE', m)
            self.assertEqual(m.args[0], 'bar', m)
            self.assertEqual(m.args[1], '<test@#test> Dies ist ein Test', m)

            self.assertEqual(self.irc.takeMsg(), None)

            with conf.supybot.plugins.AutoTrans.authorWhitelist.context(
                    ['test!*@*']):
                m = feedMsg('Dies ist ein Test')
                self.assertEqual(m.command, 'NOTICE', m)
                self.assertEqual(m.args[0], 'foo', m)
                self.assertEqual(m.args[1], '<test@#test> This is a test', m)

            self.assertEqual(self.irc.takeMsg(), None)

            with conf.supybot.plugins.AutoTrans.authorWhitelist.context(
                    ['test2!*@*']):
                m = feedMsg('Dies ist ein Test')

            self.assertEqual(self.irc.takeMsg(), None)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
