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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class Glob2Chan(callbacks.Plugin):
    def doJoin(self, irc, msg):
        channel = msg.args[0]
        if channel != '#glob2':
            return
        nick = msg.nick
        if nick.startswith('[YOG]') and \
                nick not in self.registryValue('nowelcome').split(' '):
            irc.queueMsg(ircmsgs.privmsg(nick, 'Hi %s, welcome to the '
                'globulation online game. Some people are connected from '
                'IRC if you say there name, they may answer you or start '
                'playing. For more help, type "@g2help" (without the quotes).'%
                nick))
        if nick.startswith('[YOG]'):
            irc.queueMsg(ircmsgs.IrcMsg(s='WHOIS %s' % nick))

    def do311(self, irc, msg):
        nick = msg.args[1]
        realname = msg.args[5]
        try:
            version = 'Glob2 version %s' % realname.split('-')[1]
        except:
            version = 'unknown version'
        irc.queueMsg(ircmsgs.privmsg('#glob2', 'Welcome to %s, running %s' % \
            (nick, version)))

    def g2help(self, irc, msg, args, mode):
        channel = msg.args[0]
        if channel != '#glob2':
            return
        nick = msg.nick
        if mode is None and nick.startswith('[YOG]'):
            mode = 'yog'
        elif mode is None:
            mode = 'irc'
        if not mode in ('yog', 'irc'):
            irc.error('Modes can are only "irc" and "yog"')
            return
        if mode == 'irc':
            irc.reply('(help for YOG users:) If you are feed up with getting '
                'a welcome message each time you log in, type "@nowelcome". '
                'If you want to send an automatically alert to every people '
                'who wants to play but who is not reading the chat, type '
                '"@ask4game". For more information, ask for help, with '
                'typing `!ask4help`. You can find stats about this channel '
                'at http://openihs.org:8081/global/glob2')
        elif mode == 'yog':
            irc.reply('(help for IRC users:) If you want to be notified each '
                'time someone uses "@ask4game" (game query) or "@ask4help" '
                '(help query), type "@subscribe ask4game" or "@subscribe '
                'ask4help" (depending on what you want). The opposite of '
                '"@subscribe" is "@unsubscribe".')
    g2help = wrap(g2help, [optional('somethingWithoutSpaces')])

    def nowelcome(self, irc, msg, args):
        """takes no arguments

        Disable the welcome message"""
        channel = msg.args[0]
        if channel != '#glob2':
            return
        nick = msg.nick
        if not nick.startswith('[YOG]'):
            irc.error('You are not a YOG user, so, their is no reason I send '
                'you a welcome message, but you ask me to stop sending them '
                'to you. Are you crazy?')
            return
        self.registryValue('nowelcome', value='%s %s' %
                (self.registryValue('nowelcome'), nick))
        irc.reply('I will not send you again the welcome message')
    nowelcome = wrap(nowelcome, [])

    def ask4game(self, irc, msg, args):
        """takes no arguments

        Notifies the gamers who subscribed to the alert list you want
        to play."""
        channel = msg.args[0]
        if channel != '#glob2':
            return
        online = irc.state.channels[channel].users
        gamers = self.registryValue('gamers')
        onlineGamers = [x for x in online if x in gamers]
        if len(onlineGamers) == 0:
            irc.reply('Sorry, no registered gamer is online')
            return
        irc.reply('%s: %s' % (' & '.join(onlineGamers),
                              'Someone is asking for a game!'),
                  prefixNick=False)
    ask4game = wrap(ask4game, [])

    def ask4help(self, irc, msg, args):
        """takes no arguments

        Notifies the helers who subscribed to the alert list you want
        to play."""
        channel = msg.args[0]
        if channel != '#glob2':
            return
        online = irc.state.channels[channel].users
        helpers = self.registryValue('helpers')
        onlineHelpers = [x for x in online if x in helpers]
        if len(onlineHelpers) == 0:
            irc.reply('Sorry, no registered helper is online')
            return
        irc.reply('%s: %s' % (' & '.join(onlineHelpers),
                              'Someone is asking for help!'),
                  prefixNick=False)
    ask4help = wrap(ask4help, [])

    def subscribe(self, irc, msg, args, type_):
        """{ask4game|ask4help}

        Subscribes you to the gamers/helpers alert list."""
        channel = msg.args[0]
        if channel != '#glob2':
            return
        nick = msg.nick
        print repr(type_)
        if type_ == 'ask4game':
            if nick in self.registryValue('gamers').split(' '):
                irc.error('You already subscribed to this list')
                return
            print '%s %s' % \
                (self.registryValue('gamers'), nick)
            self.setRegistryValue('gamers', value='%s %s' %
                (self.registryValue('gamers'), nick))
        elif type_ == 'ask4help':
            if nick in self.registryValue('helpers').split(' '):
                irc.error('You already subscribed to this list')
                return
            self.setRegistryValue('helpers', value='%s %s' %
                (self.registryValue('helpers'), nick))
        else:
            irc.error('The only available subscriptions are ask4game and '
                'ask4help.')
        irc.reply('I will notify you each time someone uses %s.' % type_)
    subscribe = wrap(subscribe, ['somethingWithoutSpaces'])

Class = Glob2Chan


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
