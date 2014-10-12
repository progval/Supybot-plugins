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

import time
from supybot.test import *

class TriggerTestCase(ChannelPluginTestCase):
    plugins = ('Trigger', 'Utilities')
    config = {'supybot.plugins.Trigger.triggers.join': 'echo Hi $nick',
              'supybot.plugins.Trigger.triggers.part': 'echo foo',
              'supybot.plugins.Trigger.triggers.highlight': 'echo foobar',
              'supybot.plugins.Trigger.triggers.privmsg': 'echo bar',
              'supybot.plugins.Trigger.triggers.notice': 'echo baz'}

    def _getIfAnswerIsEqual(self, msg):
        time.sleep(0.1)
        m = self.irc.takeMsg()
        while m is not None:
            if repr(m) == repr(msg):
                return True
            m = self.irc.takeMsg()
        return False

    def testBasics(self):
        self.irc.feedMsg(ircmsgs.part(self.channel, prefix=self.prefix))
        msg = ircmsgs.privmsg(self.channel, 'foo')
        self.failIf(not self._getIfAnswerIsEqual(msg), 'Does not reply to '
                'triggered echo on part')

        self.irc.feedMsg(ircmsgs.privmsg(self.channel,'lol',prefix=self.prefix))
        msg = ircmsgs.privmsg(self.channel, 'bar')
        self.failIf(not self._getIfAnswerIsEqual(msg), 'Does not reply to '
                'triggered echo on privmsg')

        self.irc.feedMsg(ircmsgs.privmsg(self.channel,'lol %s test' % self.nick,
            prefix=self.prefix))
        msg = ircmsgs.privmsg(self.channel, 'bar')
        self.failIf(not self._getIfAnswerIsEqual(msg), 'Does not reply to '
                'triggered echo on privmsg')
        msg = ircmsgs.privmsg(self.channel, 'foobar')
        self.failIf(not self._getIfAnswerIsEqual(msg), 'Does not reply to '
                'triggered echo on highlight')

        self.irc.feedMsg(ircmsgs.notice(self.channel,'lol',prefix=self.prefix))
        msg = ircmsgs.privmsg(self.channel, 'baz')
        self.failIf(not self._getIfAnswerIsEqual(msg), 'Does not reply to '
                'triggered echo on notice')

    def testSubstitute(self):
        self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        msg = ircmsgs.privmsg(self.channel, 'Hi test')
        self.failIf(not self._getIfAnswerIsEqual(msg), 'Does not welcome me')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
