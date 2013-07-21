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

import re
import time
import functools

import supybot.conf as conf
import supybot.utils as utils
import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.schedule as schedule
import supybot.registry as registry
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('AttackProtector')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

filterParser=re.compile('(?P<number>[0-9]+)p(?P<seconds>[0-9]+)')

class AttackProtectorDatabaseItem:
    def __init__(self, kind, prefix, channel, protector, irc, msg):
        self.kind = kind
        self.prefix = prefix
        self.channel = channel
        self.time = time.time()
        self.protector = protector
        value = protector.registryValue('%s.detection' % kind, channel)
        self.irc = irc
        self.msg = msg
        parsed = filterParser.match(value)
        self.expire = self.time + int(parsed.group('seconds'))

class AttackProtectorDatabase:
    def __init__(self):
        self._collections = {}

    def add(self, item):
        if item.kind not in self._collections:
            self._collections.update({item.kind: []})
        self._collections[item.kind].append(item)
        self.refresh()
        self.detectAttack(item)

    def refresh(self):
        currentTime = time.time() # Caching
        for kind in self._collections:
            collection = self._collections[kind]
            for item in collection:
                if item.expire < currentTime:
                    collection.remove(item)

    def detectAttack(self, lastItem):
        collection = self._collections[lastItem.kind]
        prefix = lastItem.prefix
        channel = lastItem.channel
        protector = lastItem.protector
        kind = lastItem.kind
        count = 0

        for item in collection:
            if item.prefix == prefix and item.channel == channel:
                count += 1
        detection = protector.registryValue(kind + '.detection', channel)
        if count >= int(filterParser.match(detection).group('number')):
            protector._slot(lastItem)
            for index, item in enumerate(collection):
                if item.prefix == prefix and item.channel == channel:
                    collection.pop(index)


class AttackProtector(callbacks.Plugin):
    """This plugin protects channels against spam and flood"""

    noIgnore = True

    def __init__(self, irc):
        self.__parent = super(AttackProtector, self)
        self.__parent.__init__(irc)
        self._enableOn = time.time() + self.registryValue('delay')
        self._database = AttackProtectorDatabase()

    def _eventCatcher(self, irc, msg, kind, **kwargs):
        if kind in ['part', 'join', 'message']:
            channels = [msg.args[0]]
            prefix = msg.prefix
        elif kind in ['knock']:
            channels = [msg.args[0]]
            prefix = msg.args[2]
        elif kind in ['nick']:
            newNick = msg.args[0]
            channels = []
            for (channel, c) in irc.state.channels.items():
                if newNick in c.users:
                    channels.append(channel)
            prefix = '*!' + msg.prefix.split('!')[1]
        elif kind in ['kicked']:
            assert 'kicked_prefix' in kwargs
            channel = msg.args[0]
            channels = [channel]
            prefix = kwargs['kicked_prefix']
        try:
            for channel in channels:
                item = None
                if not self.registryValue('%s.detection' % kind, channel) == \
                '0p0':
                    item = AttackProtectorDatabaseItem(kind, prefix, channel,
                                                       self, irc, msg)
                    self._database.add(item)

                try:
                    if not self.registryValue('group%s.detection' % kind,
                        channel) == '0p0':
                        item = AttackProtectorDatabaseItem('group%s' % kind,
                                                            '*!*@*', channel,
                                                            self, irc, msg)
                        self._database.add(item)
                except registry.NonExistentRegistryEntry:
                    pass
        except UnboundLocalError:
            pass

    def doJoin(self, irc, msg):
        self._eventCatcher(irc, msg, 'join')
    def do710(self, irc, msg):
        self._eventCatcher(irc, msg, 'knock')
    def doPart(self, irc, msg):
        self._eventCatcher(irc, msg, 'part')
    def doNick(self, irc, msg):
        self._eventCatcher(irc, msg, 'nick')
    def doPrivmsg(self, irc, msg):
        self._eventCatcher(irc, msg, 'message')
    def doNotice(self, irc, msg):
        self._eventCatcher(irc, msg, 'message')

    def _slot(self, lastItem):
        irc = lastItem.irc
        msg = lastItem.msg
        channel = lastItem.channel
        prefix = lastItem.prefix
        nick = prefix.split('!')[0]
        kind = lastItem.kind

        if not ircutils.isChannel(channel):
                return
        if not self.registryValue('enable', channel):
            return

        try:
            ircdb.users.getUser(msg.prefix) # May raise KeyError
            capability = self.registryValue('exempt')
            if capability:
                if ircdb.checkCapability(msg.prefix,
                        ','.join([channel, capability])):
                    self.log.info('Not punishing %s: they are immune.' %
                            prefix)
                    return
        except KeyError:
            pass
        punishment = self.registryValue('%s.punishment' % kind, channel)
        reason = self.registryValue('%s.kickmessage' % kind, channel)
        if not reason:
            reason = self.registryValue('kickmessage').replace('$kind', kind)

        if punishment == 'kick':
            self._eventCatcher(irc, msg, 'kicked', kicked_prefix=prefix)
        if kind == 'kicked':
            reason = _('You exceeded your kick quota.')

        banmaskstyle = conf.supybot.protocols.irc.banmask
        banmask = banmaskstyle.makeBanmask(prefix)
        if punishment == 'kick':
            msg = ircmsgs.kick(channel, nick, reason)
            irc.queueMsg(msg)
        elif punishment.startswith('ban'):
            msg = ircmsgs.ban(channel, banmask)
            irc.queueMsg(msg)

            if punishment.startswith('ban+'):
                delay = int(punishment[4:])
                unban = functools.partial(irc.queueMsg,
                        ircmsgs.unban(channel, banmask))
                schedule.addEvent(unban, delay + time.time())

        elif punishment.startswith('kban'):
            msg = ircmsgs.ban(channel, banmask)
            irc.queueMsg(msg)
            msg = ircmsgs.kick(channel, nick, reason)
            irc.queueMsg(msg)

            if punishment.startswith('kban+'):
                delay = int(punishment[5:])
                unban = functools.partial(irc.queueMsg,
                        ircmsgs.unban(channel, banmask))
                schedule.addEvent(unban, delay + time.time())

        elif punishment.startswith('mode'):
            msg = ircmsgs.mode(channel, punishment[len('mode'):])
            irc.queueMsg(msg)
        elif punishment.startswith('umode'):
            msg = ircmsgs.mode(channel, (punishment[len('umode'):], msg.nick))
            irc.queueMsg(msg)
        elif punishment.startswith('mmode'):
            msg = ircmsgs.mode(channel, (punishment[len('mmode'):], banmask))
            irc.queueMsg(msg)
        elif punishment.startswith('command '):
            tokens = callbacks.tokenize(punishment[len('command '):])
            self.Proxy(irc, msg, tokens)
AttackProtector = internationalizeDocstring(AttackProtector)


Class = AttackProtector


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
