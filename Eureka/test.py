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

from __future__ import with_statement

from supybot.test import *
import supybot.conf as conf

class EurekaTestCase(ChannelPluginTestCase):
    plugins = ('Eureka', 'User')

    _unpickleScore = re.compile(conf.supybot.plugins.Eureka.format.score() \
            .replace('$nick', '(?P<nick>[^ ]+)') \
            .replace('$score', '(?P<score>[^ ]+)'))
    def _unpickleScores(self, raw):
        rawScores = raw.split(conf.supybot.plugins.Eureka.format.separator)
        scores = {}
        for rawScore in rawScores:
            (nick, score) = _unpickleScore.group('nick', 'score')
            scores[nick] = score
        return scores

    def setUp(self):
        self.prefix1 = 'test!user@host.domain.tld'
        self.prefix2 = 'foo!bar@baz'
        self.prefix3 = 'toto!titi@tata'
        self.prefix4 = 'spam!egg@lol'
        path = conf.supybot.directories.data()
        self._path = os.path.join(os.path.abspath(path),
                'Eureka.%s.questions' % self.channel)
        ChannelPluginTestCase.setUp(self)
        with open(self._path, 'a') as fd:
            fd.write("""
            1 Who wrote this plugin?
            ---
            r ProgVal
            ---
            5 P***V**
            5 Pr**Va*
            2 Pro*Val
            === 5

            1 What is the name of this bot?
            ---
            r Limnoria
            r Supybot
            ---
            5 L******a
            2 Li****ia
            2 Lim**ria
            === 5

            1 Who is the original author of Supybot?
            ---
            r jemfinch
            ---
            === 1
            """)
        self.prefix = self.prefix1 # Just to be sure

    def testStartStop(self):
        self.assertError('scores')
        self.assertError('score')
        self.assertError('skip')
        self.assertError('stop')
        self.assertError('pause')
        self.assertError('resume')

        self.assertNotError('start')
        self.assertNotError('stop')
        self.assertNotError('start')

        self.assertError('start')
        self.assertNotError('scores')
        self.assertNotError('skip')
        self.assertError('resume')
        self.assertNotError('stop')
        self.assertNotError('start')

        self.assertNotError('pause')

        self.assertError('resume')
        self.assertNotError('pause')
        self.assertNotError('skip')

        self.assertNotError('stop')
        self.assertError('resume')

    def testBasics(self):
        msg = ircmsgs.privmsg(self.channel, 'foo', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.failUnless(self.irc.takeMsg() is None,
                'Did answer do a message while the Eureka is off.')

        msg = self._feedMsg('start')
        self.failIf(msg is None, 'did not answer to start command.')
        self.failUnless(msg.args[1] == 'Who wrote this plugin?',
                'Did ask something that is not the question: %r'%msg.args[1])

        msg = ircmsgs.privmsg(self.channel, 'foo', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.failUnless(self.irc.takeMsg() is None,
                'Did answer do a message that is not the correct answer.')

        msg = ircmsgs.privmsg(self.channel, 'ProgVal', prefix=self.prefix)
        self.irc.feedMsg(msg)
        msg = self.irc.takeMsg()
        self.failIf(msg is None,
                'Did not reply to correct answer.')
        self.failUnless(msg.args[1] == 'Congratulations test! The answer was '
                'ProgVal.',
                'Did answer %r to a correct answer.' % msg.args[1])

        msg = self.irc.takeMsg()
        self.failIf(msg is None,
                'Did not ask another question.')
        self.failUnless(msg.args[1] == 'What is the name of this bot?',
                'Did ask something that is not the question.')
        msg = ircmsgs.privmsg(self.channel, 'Limnoria', prefix=self.prefix2)
        self.irc.feedMsg(msg)
        msg = self.irc.takeMsg()
        self.failIf(msg is None,
                'Did not reply to correct answer.')
        self.failUnless(msg.args[1] == 'Congratulations foo! The answer was '
                'Limnoria. Another valid answer is: \'Supybot\'.',
                'Did answer %r to a correct answer.' % msg.args[1])

        msg = self.irc.takeMsg()
        self.failUnless(msg.args[1]=='Who is the original author of Supybot?',
                'Did ask something that is not the question.')
        time.sleep(1.5)
        msg = self.irc.takeMsg()
        self.failIf(msg is None,
                'Did not reply after timeout')
        self.failUnless(msg.args[1] == 'Nobody replied with (one of this) '
                'answer(s): jemfinch.')

    def testClues(self):
        pass
    def testTimeout(self):
        pass
    def testCaseSensitivity(self):
        pass
    def testAdjust(self):
        pass
    def testScore(self):
        pass
        

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
