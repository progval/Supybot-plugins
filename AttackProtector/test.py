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
import supybot.conf as conf
import supybot.ircdb as ircdb
import supybot.schedule as schedule

class AttackProtectorTestCase(ChannelPluginTestCase):
    plugins = ('AttackProtector', 'Config', 'Utilities', 'User')
    config = {'supybot.plugins.AttackProtector.join.detection': '5p2',
              'supybot.plugins.AttackProtector.part.punishment':
              'command echo hi !'}

    #################################
    # Utilities
    def _getIfAnswerIsEqual(self, msg):
        m = self.irc.takeMsg()
        while m is not None:
            if repr(m) == repr(msg):
                return True
            m = self.irc.takeMsg()
        return False
    def _getIfAnswerIsThisBan(self, banmask=None):
        if banmask is None:
            banmask = '*!' + (self.prefix.split('!')[1])
        return self._getIfAnswerIsEqual(ircmsgs.ban(self.channel, banmask))
    def _getIfAnswerIsThisKick(self, kind):
        reason = '%s flood detected' % kind
        return self._getIfAnswerIsEqual(ircmsgs.kick(self.channel, self.nick,
                                                 reason))
    def _getIfAnswerIsMode(self, mode):
        return self._getIfAnswerIsEqual(ircmsgs.IrcMsg(prefix="", command="MODE",
            args=(self.channel, mode)))

    #################################
    # Join tests
    def testPunishJoinFlood(self):
        for i in range(1, 5):
            msg = ircmsgs.join(self.channel, prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsThisBan() == False,
                    'No reaction to join flood.')
    def testPunishNotNoJoinFlood(self):
        for i in range(1, 4):
            msg = ircmsgs.join(self.channel, prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsThisBan(),
                    'Reaction to no join flood.')

    #################################
    # GroupJoin tests
    def testPunishGroupJoinFlood(self):
        for i in range(1, 20):
            prefix = self.prefix.split('@')
            prefix = '@'.join(['%s%i' % (prefix[0], i), prefix[1]])
            msg = ircmsgs.join(self.channel, prefix=prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsMode('+i') == False,
                    'No reaction to groupjoin flood.')
    def testPunishNotNoGroupJoinFlood(self):
        for i in range(1, 19):
            prefix = self.prefix.split('@')
            prefix = '@'.join(['%s%i' % (prefix[0], i), prefix[1]])
            msg = ircmsgs.join(self.channel, prefix=prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsMode('+i'),
                    'Reaction to no groupjoin flood.')

    #################################
    # Part tests
    def testPunishPartFlood(self):
        for i in range(1, 5):
            msg = ircmsgs.part(self.channel, prefix=self.prefix)
            self.irc.feedMsg(msg)
        msg = ircmsgs.privmsg(self.channel, 'hi !')
        self.failIf(self._getIfAnswerIsEqual(msg) == False,
                    'No reaction to part flood.')
    def testPunishNotNoPartFlood(self):
        for i in range(1, 4):
            msg = ircmsgs.part(self.channel, prefix=self.prefix)
            self.irc.feedMsg(msg)
        msg = ircmsgs.privmsg(self.channel, 'hi !')
        self.failIf(self._getIfAnswerIsEqual(msg),
                    'Reaction to no part flood.')

    #################################
    # Nick tests
    def testPunishNickFlood(self):
        for nick in 'ABCDEFG':
            msg = ircmsgs.nick(nick, prefix=self.prefix)
            self.irc.feedMsg(msg)
            self.prefix = nick + '!' + self.prefix.split('!')[1]
        banmask = '*!' + self.prefix.split('!')[1]
        self.failIf(self._getIfAnswerIsThisBan(banmask) == False,
                    'No reaction to nick flood.')
    def testPunishNotNoNickFlood(self):
        for nick in 'ABCDEF':
            msg = ircmsgs.nick(nick, prefix=self.prefix)
            self.irc.feedMsg(msg)
            self.prefix = nick + '!' + self.prefix.split('!')[1]
        banmask = '*!' + self.prefix.split('!')[1]
        self.failIf(self._getIfAnswerIsThisBan(banmask),
                    'Reaction to no nick flood.')

    #################################
    # Message tests
    def testPunishMessageFlood(self):
        for i in range(1, 11):
            msg = ircmsgs.privmsg(self.channel, 'Hi, this is a flood',
                                  prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsThisKick('message') == False,
                    'No reaction to privmsg flood.')
    def testPunishNoticeFlood(self):
        for i in range(1, 11):
            msg = ircmsgs.notice(self.channel, 'Hi, this is a flood',
                                  prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsThisKick('message') == False,
                    'No reaction to notice flood.')
    def testPunishNotNoMessageFlood(self):
        for i in range(1, 10):
            msg = ircmsgs.privmsg(self.channel, 'Hi, this is a flood',
                                  prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsThisKick('message'),
                   'Reaction to no privmsg flood.')
    def testPunishNotNoNoticeFlood(self):
        for i in range(1, 10):
            msg = ircmsgs.notice(self.channel, 'Hi, this is a flood',
                                  prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsThisKick('message'),
                   'Reaction to no notice flood.')
    def testPunishNoticeFlood(self):
        for i in range(1, 6):
            msg = ircmsgs.notice(self.channel, 'Hi, this is a flood',
                                  prefix=self.prefix)
            self.irc.feedMsg(msg)
            msg = ircmsgs.privmsg(self.channel, 'Hi, this is a flood',
                                  prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.failIf(self._getIfAnswerIsThisKick('message') == False,
                    'No reaction to both notice and privmsg flood.')

    #################################
    # Test trusted users
    def testDoesNotPunishTrustedUsers(self):
        feedMsg = PluginTestCase.feedMsg
        feedMsg(self, 'register toto foobarbaz')
        feedMsg(self, 'identify toto foobarbaz')
        [self.irc.takeMsg() for x in 'xx']
        self.assertNotError('eval '
                '''"ircdb.users.getUser(1).capabilities.add('nopunish')"''')
        self.assertResponse('capabilities', '[nopunish]')

        try:
            for i in range(1, 5):
                msg = ircmsgs.join(self.channel, prefix=self.prefix)
                self.irc.feedMsg(msg)
            self.failIf(self._getIfAnswerIsThisBan(), 'Punishes trusted user')
        finally:
            feedMsg(self, 'hostmask remove toto %s' % self.prefix)
            feedMsg(self, 'unidentify') # Otherwise, other tests would fail
            [self.irc.takeMsg() for x in 'xx']
            self.assertNotRegexp('whoami', 'toto')
            self.assertError('capabilities')

    #################################
    # Test punishments

    def testDisable(self):
        for i in range(1, 11):
            msg = ircmsgs.privmsg(self.channel, 'Hi, this is a flood',
                                  prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.assertNotError('config plugins.AttackProtector.message.punishment '
                'umode+b')
        return self._getIfAnswerIsEqual(ircmsgs.IrcMsg(prefix="", command="MODE",
            args=(self.channel, mode, self.nick)))

    def testKban(self):
        def run_schedule():
            while schedule.schedule.schedule:
                schedule.run()
        with conf.supybot.plugins.AttackProtector.message.punishment.context(
                'kban+2'):
            for i in range(1, 11):
                msg = ircmsgs.privmsg(self.channel, 'Hi, this is a flood',
                                      prefix=self.prefix)
                self.irc.feedMsg(msg)
            m = self.irc.takeMsg()
            self.assertEqual(m.command, 'MODE')
            m = self.irc.takeMsg()
            self.assertEqual(m.command, 'KICK')
            self.assertEqual(self.irc.takeMsg(), None)
            threading.Thread(target=run_schedule).start()
            self.assertEqual(self.irc.takeMsg(), None)
            time.sleep(1)
            self.assertEqual(self.irc.takeMsg(), None)
            time.sleep(2)
            m = self.irc.takeMsg()
            self.assertEqual(m.command, 'MODE')
        schedule.schedule.schedule = False

    #################################
    # 'Kicked' tests
    def testKbanAfterKicks(self):
        prefix = 'testing!Attack@Protector'
        self.assertNotError('config plugins.AttackProtector.groupmessage.detection 100p10')
        for i in range(1, 5):
            for i in range(1, 11):
                msg = ircmsgs.privmsg(self.channel, 'Hi, this is a flood',
                                      prefix=prefix)
                self.irc.feedMsg(msg)
            m = self.irc.takeMsg()
            self.assertEqual(m.command, 'KICK')
        for i in range(1, 11):
            msg = ircmsgs.privmsg(self.channel, 'Hi, this is a flood',
                                  prefix=prefix)
            self.irc.feedMsg(msg)
        self.assertEqual(self.irc.takeMsg().command, 'MODE')

    #################################
    # Global tests
    def testCleanCollection(self):
        for i in range(1, 4):
            self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        time.sleep(3)
        self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        self.failIf(self._getIfAnswerIsThisBan(),
                    'Doesn\'t clean the join collection.')

    def testDontCleanCollectionToEarly(self):
        for i in range(1, 4):
            self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        time.sleep(1)
        self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        self.failIf(self._getIfAnswerIsThisBan() == False,
                    'Cleans the collection before it should be cleaned')

    def testCleanCollectionAfterPunishment(self):
        for i in range(1, 6):
            self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        self._getIfAnswerIsThisBan()
        self.irc.feedMsg(ircmsgs.join(self.channel, prefix=self.prefix))
        self.failIf(self._getIfAnswerIsThisBan(),
                    'Doesn\'t clean the join collection after having banned.')

    def testDisable(self):
        for i in range(1, 11):
            msg = ircmsgs.privmsg(self.channel, 'Hi, this is a flood',
                                  prefix=self.prefix)
            self.irc.feedMsg(msg)
        self.assertNotError('config plugin.AttackProtector.enable False')
        self.failIf(self._getIfAnswerIsThisKick('message'),
                    'Punishment even if disabled')



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
