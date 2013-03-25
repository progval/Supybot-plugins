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
import supybot.schedule as schedule

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
    def _clearMsg(self):
        msg = 1
        while msg is not None:
            msg = self.irc.takeMsg()

    def setUp(self):
        # Avoid conflicts between tests.
        # We use .keys() in order to prevent this error:
        # RuntimeError: dictionary changed size during iteration
        for name in list(schedule.schedule.events.keys()):
            schedule.removeEvent(name)
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
            2 Who wrote this plugin?
            ---
            r ProgVal
            ---
            5 P***V**
            5 Pr**Va*
            2 Pro*Val
            === 5

            4 What is the name of this bot?
            ---
            r Limnoria
            r Supybot
            ---
            5 L******a
            2 Li****ia
            2 Lim**ria
            === 5

            3 Who is the original author of Supybot?
            ---
            r jemfinch
            ---
            1 j*******
            1 jem*****
            === 1

            1 Give a number.
            ---
            r 42
            m [0-9]+
            ---
            === 2

            1 Give another number.
            ---
            r 42
            m [0-9]+
            ---
            === 2
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
        self._clearMsg()
        self.assertNotError('stop')
        self.assertNotError('start')
        self._clearMsg()

        self.assertError('start')
        self.assertNotError('scores')
        self.assertNotError('skip')
        self.assertError('resume')
        self.assertNotError('stop')
        self.assertNotError('start')

        self.assertNotError('pause')

        self.assertNotError('resume')
        self.assertError('resume')
        self.assertNotError('pause')
        self.assertError('pause')
        self.assertNotError('skip')

        self.assertNotError('stop')
        self.assertError('resume')

    def testBasics(self):
        msg = ircmsgs.privmsg(self.channel, 'foo', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertNoResponse(' ')

        self.assertResponse('start', 'Who wrote this plugin?')

        msg = ircmsgs.privmsg(self.channel, 'foo', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertNoResponse(' ')

        msg = ircmsgs.privmsg(self.channel, 'ProgVal', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertResponse(' ', 'Congratulations test! The answer was '
                '\'ProgVal\'.')

        self.assertResponse(' ', 'What is the name of this bot?')
        msg = ircmsgs.privmsg(self.channel, 'Limnoria', prefix=self.prefix2)
        self.irc.feedMsg(msg)
        self.assertResponse(' ', 'Congratulations foo! The answer was '
                '\'Limnoria\'. Another valid answer is: \'Supybot\'.')

        self.assertResponse(' ', 'Who is the original author of Supybot?')
        self.timeout = 0.2
        self.assertNoResponse(' ', 0.9)
        self.assertResponse(' ', 'Another clue: j*******')
        self.assertNoResponse(' ', 0.9)
        self.assertResponse(' ', 'Another clue: jem*****')
        self.assertNoResponse(' ', 0.9)
        self.assertResponse(' ', 'Nobody replied with (one of this) '
                'answer(s): \'jemfinch\'.')

        self.timeout = 1
        self.assertResponse(' ', 'Give a number.')
        msg = ircmsgs.privmsg(self.channel, 'foo', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertNoResponse(' ')
        msg = ircmsgs.privmsg(self.channel, '12', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertResponse(' ', 'Congratulations test! The answer was \'12\'. '
                'Another valid answer is: \'42\'.')

        self.timeout = 1
        self.assertResponse(' ', 'Give another number.')
        msg = ircmsgs.privmsg(self.channel, 'foo', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertNoResponse(' ')
        msg = ircmsgs.privmsg(self.channel, '42', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertResponse(' ', 'Congratulations test! The answer was '
                '\'42\'.')

        self.assertError('stop')
        self.assertError('pause')
        self.assertError('resume')
        self.assertNotError('start')

    def testCaseSensitivity(self):
        self.assertNotError('start')
        self._clearMsg()
        msg = ircmsgs.privmsg(self.channel, 'PROGVAL', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertResponse(' ', 'Congratulations test! The answer was '
                '\'ProgVal\'.')
    def testAdjust(self):
        self.assertNotError('start')
        self.assertRegexp('scores', 'noone')
        self.assertError('score foo')
        self.assertError('score bar')
        self.assertError('score baz')
        self.assertNotError('adjust foo 5')
        self.assertResponse('scores', 'foo(5)')
        self.assertResponse('score foo', '5')
        self.assertError('score bar')
        self.assertError('score baz')
        self.assertNotError('adjust bar 2')
        self.assertResponse('scores', 'foo(5), bar(2)')
        self.assertResponse('score foo', '5')
        self.assertResponse('score bar', '2')
        self.assertError('score baz')
        self.assertNotError('adjust bar 7')
        self.assertResponse('scores', 'bar(9), foo(5)')
        self.assertResponse('score foo', '5')
        self.assertResponse('score bar', '9')
        self.assertError('score baz')
    def testClue(self):
        self.timeout = 0.2
        self.assertResponse('start', 'Who wrote this plugin?')
        self.assertResponse('clue', 'Another clue: P***V**')
    def testScore(self):
        self.assertNotError('start')
        self.assertRegexp('scores', 'noone')
        self.assertError('score test')
        msg = ircmsgs.privmsg(self.channel, 'foo', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self.assertRegexp('scores', 'noone')
        self.assertError('score test')
        msg = ircmsgs.privmsg(self.channel, 'ProgVal', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self._clearMsg()
        self.assertResponse('scores', 'test(2)')
        msg = ircmsgs.privmsg(self.channel, 'ProgVal', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self._clearMsg()
        self.assertResponse('scores', 'test(2)')
        self.prefix = self.prefix2
        msg = ircmsgs.privmsg(self.channel, 'supybot', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self._clearMsg()
        self.assertResponse('scores', 'foo(4), test(2)')
        self.prefix = self.prefix1
        msg = ircmsgs.privmsg(self.channel, 'jemfinch', prefix=self.prefix)
        self.irc.feedMsg(msg)
        self._clearMsg()
        self.assertResponse('scores', 'test(5), foo(4)')



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
