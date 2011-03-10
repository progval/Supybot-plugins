# -*- coding: utf8 -*-
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

class NoLatin1TestCase(ChannelPluginTestCase):
    plugins = ('NoLatin1',)
    config = {'supybot.reply.whenNotCommand': False,
              'supybot.plugins.NoLatin1.enable': True,
              'supybot.plugins.NoLatin1.remember': 2}

    def testNoLatin1(self):
        for foo in range(0, 4):
            self.assertRegexp('blah \xe9 blah', 'Please use.*')
        self.assertRegexp('blah \xe9 blah', 'User test is still.*')
        self.assertRegexp('blah \xe9 blah', 'Please use.*')

    def testNoWarningOnUnicode(self):
        msg = ircmsgs.privmsg(self.channel, 'Hi !', prefix=self.prefix)
        self.irc.feedMsg(msg)
        msg = self.irc.takeMsg()
        assert msg is None, msg
        msg = ircmsgs.privmsg(self.channel, 'é', prefix=self.prefix)
        self.irc.feedMsg(msg)
        msg = self.irc.takeMsg()
        assert msg is None, msg

    def testCleanUp(self):
        for foo in range(0, 4):
            self.assertRegexp('blah \xe9 blah', 'Please use.*')
        time.sleep(3)
        self.assertRegexp('blah \xe9 blah', 'Please use.*')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
