# -*- coding: utf8 -*-
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

class GoodFrenchTestCase(ChannelPluginTestCase):
    plugins = ('GoodFrench',)
    config = {'plugins.GoodFrench.level': 7, 'plugins.GoodFrench.kick': True}

    def _isKicked(self):
        m = self.irc.takeMsg()
        while m is not None:
            if m.command == 'KICK':
                return True
            m = self.irc.takeMsg()
        return False

    _bad = "C tt"
    _good = "C'est tout"

    def testDetect(self):
        self.assertRegexp("GoodFrench detect %s" % self._bad, 'erreurs : ')
        self.assertRegexp("GoodFrench detect %s" % self._good, 'correcte')

    def testKick(self):
        msg = ircmsgs.privmsg(self.channel, self._bad,
                              prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.failIf(self._isKicked() == False, 'Not kicked on misspell')

        msg = ircmsgs.privmsg(self.channel, self._good,
                              prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.failIf(self._isKicked(), 'Kicked on correct sentence')

    def assertMistake(self, text):
        try:
            self.assertRegexp("GoodFrench detect %s" % text, 'erreurs? : ')
        except AssertionError as e:
            print text
            raise e

    def testMistakes(self):
        for text in ["je suis pas là", "j'ai pas faim", "j'ait", "je ait",
                     "il es", "quel est la", "quelle est le",
                     "C'est bon; il est parti", "C'est bon , il est parti",
                     "C'est bon ,il est parti", "C'est bon ;il est parti",
                     "lol", "loooool", "LOOO00ool", "10001"]:
            self.assertMistake(text)

    def assertNoMistake(self, text):
        try:
            self.assertRegexp("GoodFrench detect %s" % text, 'correcte')
        except AssertionError as e:
            print text
            raise e

    def testNotMistakes(self):
        for text in ["je ne suis pas là", "je n'ai pas faim", "j'ai",
                     "il est", "quelle est la", "quel est le", "je sais",
                     "C'est bon ; il est parti", "C'est bon, il est parti"]:
            self.assertNoMistake(text)



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
