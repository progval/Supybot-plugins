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

import time
from supybot.test import *

class AttackProtectorTestCase(ChannelPluginTestCase):
    plugins = ('AttackProtector',)
    def _getIfBanned(self):
        m = self.irc.takeMsg()
        while m is not None:
            if m == ircmsgs.ban(self.channel, self.prefix):
                return True
            m = self.irc.takeMsg()
        return False
        
    
    def testPunishJoinFlood(self):
        for i in range(1, 5):
            self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        self.failIf(self._getIfBanned() == False, 'No reaction to join flood.')

    def testPunishNotNoJoinFlood(self):
        for i in range(1,4):
            self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        self.failIf(self._getIfBanned(), 'Reaction to no join flood.')

    def testCleanCollection(self):
        for i in range(1, 4):
            self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        time.sleep(6)
        self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        self.failIf(self._getIfBanned(), 'Doesn\'t clean the join collection.')

    def testDontCleanCollectionToEarly(self):
        for i in range(1, 4):
            self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        time.sleep(2)
        self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        self.failIf(self._getIfBanned() == False, 'Cleans the collection '
                                         'before it should be cleaned')
        


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
