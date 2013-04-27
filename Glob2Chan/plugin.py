# -*- coding: utf8 -*-
###
# Copyright (c) 2010-2011, Valentin Lorentz
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

from __future__ import unicode_literals

from django.contrib.gis.geoip import GeoIP

import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.httpserver as httpserver

class Glob2ChanCallback(httpserver.SupyHTTPServerCallback):
    name = "Glob2 server notifications"
    defaultResponse = """
    You shouldn't be there, this subfolder is not for you. Go back to the
    index and try out other plugins (if any)."""
    def doGet(self, handler, path):
        host = handler.address_string()
        if host == 'localhost':
            assert path.startswith('/status/')
            status = path[len('/status/'):].replace('/', ' ')
            self.plugin._announce(ircutils.bold('[YOG]') +
                    ' YOG server at %s is %s.' % (host, status))
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('Channel notified.')
        else:
            self.send_response(403)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('Not authorized.')

instance = None

class Glob2Chan(callbacks.Plugin):
    def __init__(self, irc):
        global instance
        self.__parent = super(Glob2Chan, self)
        callbacks.Plugin.__init__(self, irc)
        instance = self

        callback = Glob2ChanCallback()
        callback.plugin = self
        httpserver.hook('glob2', callback)
        self._users = {}
    def die(self):
        self.__parent.die()
        httpserver.unhook('glob2')

    def _announce(self, message):
        for irc in world.ircs:
            if '#glob2' in irc.state.channels:
                break
        assert '#glob2' in irc.state.channels
        irc.queueMsg(ircmsgs.privmsg('#glob2', message))

    def doJoin(self, irc, msg):
        channel = msg.args[0]
        if channel != '#glob2':
            return
        nick = msg.nick
        self._users.update({msg.nick: msg.prefix.split('@')[1]})
        if nick.startswith('[YOG]'):
            irc.queueMsg(ircmsgs.IrcMsg(s='WHOIS %s' % nick))

    def do311(self, irc, msg):
        nick = msg.args[1]
        if not nick.startswith('[YOG]') or nick in self.registryValue('nowelcome').split(' '):
            return
        realname = msg.args[5]
        hostname = self._users.pop(nick)
        try:
            version = 'Glob2 version %s' % realname.split('-')[1]
        except:
            version = 'unknown version'
        g = GeoIP()
        country = g.country(hostname)['country_name']
        if country == 'France':
            irc.queueMsg(ircmsgs.privmsg(nick, ('Bonjour %s, bienvenue dans le '
                'salon de jeu Globulation2 en ligne. Il y a actuellement %i '
                'personnes connectées via IRC, elles pourraient se réveiller et '
                'jouer avec vous. Attendez ici au moins quelques minutes, '
                'quelqu\'un pourrait se connecter d\'ici là.') %
                (nick, len(irc.state.channels['#glob2'].users))))
        else:
            irc.queueMsg(ircmsgs.privmsg(nick, ('Hi %s, welcome to the '
                'globulation online game room. There are currently %i '
                'people connected via IRC, they may awaken and challenge '
                'you to a game. Please stay here at least a few minutes, '
                'someone may connect in the meantime.') %
                (nick, len(irc.state.channels['#glob2'].users))))
        irc.queueMsg(ircmsgs.privmsg('#glob2', ('Welcome to %s, running %s '
            'and connecting from %s.') % (nick, version, country)))

    def g2help(self, irc, msg, args, mode):
        """[{irc|yog}]

        Prints help for IRC/YOG users."""
        channel = msg.args[0]
        if channel != '#glob2':
            return
        nick = msg.nick
        if mode is None and nick.startswith('[YOG]'):
            mode = 'yog'
        elif mode is None:
            mode = 'irc'
        if mode == 'yog':
            irc.reply('\x02(help for YOG users:)\x02 If you are fed up with '
                'getting a welcome message each time you log in, type '
                '"\x02@nowelcome\x02". '
                'If you want to send an automatic alert to everybody '
                'who wants to play but who is not reading the chat, type '
                '"\x02@ask4game\x02". For more information, ask for help, with '
                'typing "\x02@ask4help\x02".')
        elif mode == 'irc':
            irc.reply('\x02(help for IRC users:)\x02 If you want to be notified each '
                'time someone uses "\x02@ask4game\x02" (game query) or "\x02@ask4help\x02" '
                '(help query), type "\x02@subscribe ask4game\x02" or "\x02@subscribe '
                'ask4help\x02" (depending on what you want). The opposite of '
                '"\x02@subscribe\x02" is "\x02@unsubscribe\x02".')
        else:
            irc.error('Modes can are only "irc" and "yog"')
        irc.reply('I am a Supybot-powered IRC bot. Don\'t try to talk or play '
                  'with me ;) If you have questions, bug reports, feature '
                  'requests, ... ask my owner, he is \x02ProgVal\x02. '
                  'You can find stats about this channel '
                  'at \x02http://openihs.org:7412/webstats/global/glob2/\x02')
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
        self.setRegistryValue('nowelcome', value='%s %s' %
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
        onlineGamers = [x for x in online if x in gamers and x != msg.nick]
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
        onlineHelpers = [x for x in online if x in helpers and x != msg.nick]
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
        if type_ == 'ask4game':
            if nick in self.registryValue('gamers').split(' '):
                irc.error('You already subscribed to this list')
                return
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

    def unsubscribe(self, irc, msg, args, type_):
        """{ask4game|ask4help}

        Unsubscribes you from the gamers/helpers alert list."""
        channel = msg.args[0]
        if channel != '#glob2':
            return
        nick = msg.nick
        if type_ == 'ask4game':
            if nick not in self.registryValue('gamers').split(' '):
                irc.error('You didn\'t subscribe to this list')
                return
            nickslist = self.registryValue('gamers').split(' ')
            nickslist.remove(nick)
            self.setRegistryValue('gamers', value=' '.join(nickslist))
        elif type_ == 'ask4help':
            if nick in self.registryValue('helpers').split(' '):
                irc.error('You didn\'t subscribe to this list')
                return
            nickslist = self.registryValue('helpers').split(' ')
            nickslist.remove(nick)
            self.setRegistryValue('helpers', value=' '.join(nickslist))
        else:
            irc.error('The only available unsubscriptions are ask4game and '
                'ask4help.')
        irc.reply('I won\'t notify you each time someone uses %s anymore.' %
                  type_)
    unsubscribe = wrap(unsubscribe, ['somethingWithoutSpaces'])

Class = Glob2Chan


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
