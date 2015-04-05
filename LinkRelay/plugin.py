###
# Copyright (c) 2010, quantumlemur
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

import re
import copy
import string
import supybot.log as log
import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.irclib as irclib
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.registry as registry
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('LinkRelay')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

@internationalizeDocstring
class LinkRelay(callbacks.Plugin):
    """Advanced message relay between channels."""
    noIgnore = True
    threaded = True

    class Relay():
        def __init__(self, sourceChannel, sourceNetwork, targetChannel,
                     targetNetwork, channelRegex, networkRegex, messageRegex):
            self.sourceChannel = sourceChannel
            self.sourceNetwork = sourceNetwork
            self.targetChannel = targetChannel
            self.targetNetwork = targetNetwork
            self.channelRegex = channelRegex
            self.networkRegex = networkRegex
            self.messageRegex = messageRegex


    def __init__(self, irc):
        self.__parent = super(LinkRelay, self)
        self.__parent.__init__(irc)
        self._loadFromConfig()
        self.ircstates = {}
        try:
            conf.supybot.plugins.LinkRelay.substitutes.addCallback(
                    self._loadFromConfig)
            conf.supybot.plugins.LinkRelay.relays.addCallback(
                    self._loadFromConfig)
        except registry.NonExistentRegistryEntry:
            log.error("Your version of Supybot is not compatible with "
                      "configuration hooks. So, LinkRelay won't be able "
                      "to reload the configuration if you use the Config "
                      "plugin.")

    def _loadFromConfig(self, name=None):
        self.relays = []
        for relay in self.registryValue('relays').split(' || '):
            if relay.endswith('|'):
                relay += ' '
            relay = relay.split(' | ')
            if not len(relay) == 5:
                continue
            try:
                self.relays.append(self.Relay(relay[0],
                                          relay[1],
                                          relay[2],
                                          relay[3],
                                          re.compile('^%s$' % relay[0], re.I),
                                          re.compile('^%s$' % relay[1], re.I),
                                          re.compile(relay[4])))
            except:
                log.error('Failed adding relay: %r' % relay)

        self.nickSubstitutions = {}
        for substitute in self.registryValue('substitutes').split(' || '):
            if substitute.endswith('|'):
                substitute += ' '
            substitute = substitute.split(' | ')
            if not len(substitute) == 2:
                continue
            self.nickSubstitutions[substitute[0]] = substitute[1]



    def simpleHash(self, s):
        colors = ["\x0305", "\x0304", "\x0303", "\x0309", "\x0302", "\x0312",
                  "\x0306",   "\x0313", "\x0310", "\x0311", "\x0307"]
        num = 0
        for i in s:
            num += ord(i)
        num = num % 11
        return colors[num]


    def getPrivmsgData(self, channel, nick, text, colored):
        color = self.simpleHash(nick)
        if nick in self.nickSubstitutions:
            nick = self.nickSubstitutions[nick]
        if not self.registryValue('nicks', channel):
            nick = ''
        if re.match('^\x01ACTION .*\x01$', text):
            text = text.strip('\x01')
            text = text[ 7 : ]
            if colored:
                return ('* \x03%(color)s%(nick)s%(network)s\017 %(text)s',
                        {'nick': nick, 'color': color, 'text': text})
            else:
                return ('* %(nick)s%(network)s %(text)s',
                        {'nick': nick, 'text': text})
        else:
            if colored:
                return ('<\x03%(color)s%(nick)s%(network)s\017> %(text)s',
                        {'color': color, 'nick': nick, 'text': text})
            else:
                return ('<%(nick)s%(network)s> %(text)s',
                        {'nick': nick, 'text': text})
        return s


    @internationalizeDocstring
    def list(self, irc, msg, args):
        """takes no arguments

        Returns all the defined relay links"""
        if not self.relays:
            irc.reply(_('This is no relay enabled. Use "linkrelay add" to '
                'add one.'))
            return
        replies = []
        for relay in self.relays:
            if world.getIrc(relay.targetNetwork):
                hasIRC = 'Link healthy!'
            else:
                hasIRC = '\x03%sNot connected to network.\017' % \
                        self.registryValue('colors.info', msg.args[0])
            s ='\x02%s\x02 on \x02%s\x02 ==> \x02%s\x02 on \x02%s\x02.  %s'
            if not self.registryValue('color', msg.args[0]):
                s = s.replace('\x02', '')
            replies.append(s %
                        (relay.sourceChannel,
                         relay.sourceNetwork,
                         relay.targetChannel,
                         relay.targetNetwork,
                         hasIRC))
        irc.replies(replies)

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        s = msg.args[1]
        s, args = self.getPrivmsgData(channel, msg.nick, s,
                               self.registryValue('color', channel))
        if channel not in irc.state.channels: # in private
            # cuts off the end of commands, so that passwords
            # won't be revealed in relayed PM's
            if callbacks.addressed(irc.nick, msg):
                if self.registryValue('color', channel):
                    color = '\x03' + self.registryValue('colors.truncated',
                            channel)
                    match = '(>\017 \w+) .*'
                else:
                    color = ''
                    match = '(> \w+) .*'
                s = re.sub(match, '\\1 %s[%s]' % (color, _('truncated')), s)
            s = '(via PM) %s' % s
        self.sendToOthers(irc, channel, s, args, isPrivmsg=True)


    def outFilter(self, irc, msg):
        if msg.command == 'PRIVMSG':
            if not msg.relayedMsg:
                if msg.args[0] in irc.state.channels:
                    s, args = self.getPrivmsgData(msg.args[0], irc.nick, msg.args[1],
                                    self.registryValue('color', msg.args[0]))
                    self.sendToOthers(irc, msg.args[0], s, args, isPrivmsg=True)
        return msg


    def doMode(self, irc, msg):
        args = {'nick': msg.nick, 'channel': msg.args[0],
                'mode': ' '.join(msg.args[1:]), 'color': ''}
        if self.registryValue('color', msg.args[0]):
            args['color'] = '\x03%s' % self.registryValue('colors.mode', msg.args[0])
        s = '%(color)s' + _('*/* %(nick)s changed mode on '
                '%(channel)s%(network)s to %(mode)s')
        self.sendToOthers(irc, msg.args[0], s, args)

    def doJoin(self, irc, msg):
        args = {'nick': msg.nick, 'channel': msg.args[0], 'color': ''}
        if self.registryValue('color', msg.args[0]):
            args['color'] = '\x03%s' % self.registryValue('colors.join', msg.args[0])
        if self.registryValue('hostmasks', msg.args[0]):
            args['nick'] = msg.prefix
        s = '%(color)s' + _('--> %(nick)s has joined %(channel)s%(network)s')
        self.sendToOthers(irc, msg.args[0], s, args)

    def doPart(self, irc, msg):
        args = {'nick': msg.nick, 'channel': msg.args[0], 'color': ''}
        if self.registryValue('color', msg.args[0]):
            args['color'] = '\x03%s' % self.registryValue('colors.part', msg.args[0])
        if self.registryValue('hostmasks', msg.args[0]):
            args['nick'] = msg.prefix
        s = '%(color)s' + _('<-- %(nick)s has left %(channel)s%(network)s')
        self.sendToOthers(irc, msg.args[0], s, args)

    def doKick(self, irc, msg):
        args = {'kicked': msg.args[1], 'channel': msg.args[0],
                'kicker': msg.nick, 'message': msg.args[2], 'color': ''}
        if self.registryValue('color', msg.args[0]):
            args['color'] = '\x03%s' % self.registryValue('colors.kick',
                    msg.args[0])
        s = '%(color)s' + _('<-- %(kicked)s has been kicked from '
                '%(channel)s%(network)s by %(kicker)s (%(message)s)')
        self.sendToOthers(irc, msg.args[0], s, args)

    def doNick(self, irc, msg):
        args = {'oldnick': msg.nick, 'network': irc.network,
                'newnick': msg.args[0], 'color': ''}
        if self.registryValue('color', msg.args[0]):
            args['color'] = '\x03%s' % self.registryValue('colors.nick', msg.args[0])
        s = _('*/* %(oldnick)s (%(network)s) changed their nickname to '
                '%(newnick)s')
        for (channel, c) in irc.state.channels.items():
            if msg.args[0] in c.users:
                self.sendToOthers(irc, channel, s, args)

    def doQuit(self, irc, msg):
        args = {'nick': msg.nick, 'network': irc.network,
                'message': msg.args[0], 'color': ''}
        if self.registryValue('color', msg.args[0]):
            args['color'] = '\x03%s' % self.registryValue('colors.quit', msg.args[0])
        s = _('<-- %(nick)s has quit on %(network)s (%(message)s)')
        self.sendToOthers(irc, None, s, args, msg.nick)

    def sendToOthers(self, irc, channel, s, args, nick=None, isPrivmsg=False):
        assert channel is not None or nick is not None
        def format_(relay, s, args):
            if 'network' not in args:
                if self.registryValue('includeNetwork', relay.targetChannel):
                    args['network'] = '@' + irc.network
                else:
                    args['network'] = ''
            return s % args
        def send(s):
            targetIRC = world.getIrc(relay.targetNetwork)
            if not targetIRC:
                self.log.info('LinkRelay:  Not connected to network %s.' %
                              relay.targetNetwork)
            elif targetIRC.zombie:
                self.log.info('LinkRelay:  IRC %s appears to be a zombie'%
                              relay.targetNetwork)
            elif irc.isChannel(relay.targetChannel) and \
                    relay.targetChannel not in targetIRC.state.channels:
                self.log.info('LinkRelay:  I\'m not in in %s on %s' %
                              (relay.targetChannel, relay.targetNetwork))
            else:
                if isPrivmsg or \
                        self.registryValue('nonPrivmsgs', channel) == 'privmsg':
                    f = ircmsgs.privmsg
                elif self.registryValue('nonPrivmsgs', channel) == 'notice':
                    f = ircmsgs.notice
                else:
                    return
                allowedLength = conf.get(conf.supybot.reply.mores.length,
                         relay.targetChannel) or 470
                cont = _('(continuation)')
                remainingLength = allowedLength - len(cont) - 1
                head = s[0:allowedLength]
                tail = [cont + ' ' + s[i:i+remainingLength] for i in
                        range(allowedLength, len(s), remainingLength)]
                for s in [head] + tail:
                    msg = f(relay.targetChannel, s)
                    msg.tag('relayedMsg')
                    targetIRC.sendMsg(msg)

        if channel is None:
            for relay in self.relays:
                for channel in relay.sourceIRCChannels:
                    new_s = format_(relay, s, args)
                    if nick in relay.sourceIRCChannels[channel].users and \
                            relay.channelRegex.match(channel) and \
                            relay.networkRegex.match(irc.network)and \
                            relay.messageRegex.search(new_s):
                        send(new_s)
        else:
            for relay in self.relays:
                new_s = format_(relay, s, args)
                if relay.channelRegex.match(channel) and \
                        relay.networkRegex.match(irc.network)and \
                        relay.messageRegex.search(new_s):
                    send(new_s)
        for relay in self.relays:
            if relay.sourceNetwork == irc.network:
                relay.sourceIRCChannels = copy.deepcopy(irc.state.channels)


    @internationalizeDocstring
    def nicks(self, irc, msg, args, channel):
        """[<channel>]

        Returns the nicks of the people in the linked channels.
        <channel> is only necessary if the message
        isn't sent on the channel itself."""
        for relay in self.relays:
            if relay.sourceChannel == channel and \
                    relay.sourceNetwork.lower() == irc.network.lower():
                if not world.getIrc(relay.targetNetwork):
                    irc.reply(_('Not connected to network %s.') %
                              relay.targetNetwork)
                else:
                    users = []
                    ops = []
                    halfops = []
                    voices = []
                    normals = []
                    numUsers = 0
                    target = relay.targetChannel

                    channels = world.getIrc(relay.targetNetwork).state.channels
                    found = False
                    for key, channel_ in channels.items():
                        if re.match(relay.targetChannel, key):
                            found = True
                            break
                    if not found:
                        continue

                    for s in channel_.users:
                        s = s.strip()
                        if not s:
                            continue
                        numUsers += 1
                        if s in channel_.ops:
                            users.append('@%s' % s)
                        elif s in channel_.halfops:
                            users.append('%%%s' % s)
                        elif s in channel_.voices:
                            users.append('+%s' % s)
                        else:
                            users.append(s)
                    #utils.sortBy(ircutils.toLower, ops)
                    #utils.sortBy(ircutils.toLower, halfops)
                    #utils.sortBy(ircutils.toLower, voices)
                    #utils.sortBy(ircutils.toLower, normals)
                    users.sort()
                    msg.tag('relayedMsg')
                    s = _('%d users in %s on %s:  %s') % (numUsers,
                            relay.targetChannel,
                            relay.targetNetwork,
                            utils.str.commaAndify(users))
                    irc.reply(s)
        irc.noReply()
    nicks = wrap(nicks, ['Channel'])


    # The fellowing functions handle configuration
    def _writeToConfig(self, from_, to, regexp, add):
        from_, to = from_.split('@'), to.split('@')
        args = from_
        args.extend(to)
        args.append(regexp)
        s = ' | '.join(args)

        currentConfig = self.registryValue('relays')
        config = list(map(ircutils.IrcString, currentConfig.split(' || ')))
        if add:
            if s in config:
                return False
            if currentConfig == '':
                self.setRegistryValue('relays', value=s)
            else:
                self.setRegistryValue('relays',
                                      value=' || '.join((currentConfig, s)))
        else:
            if s not in config:
                return False
            config.remove(s)
            self.setRegistryValue('relays', value=' || '.join(config))
        return True

    def _parseOptlist(self, irc, msg, tupleOptlist):
        optlist = {}
        for key, value in tupleOptlist:
            optlist.update({key: value})
        if 'from' not in optlist and 'to' not in optlist:
            irc.error(_('You must give at least --from or --to.'))
            return
        for name in ('from', 'to'):
            if name not in optlist:
                optlist.update({name: '%s@%s' % (msg.args[0], irc.network)})
        if 'regexp' not in optlist:
            optlist.update({'regexp': ''})
        if 'reciprocal' in optlist:
            optlist.update({'reciprocal': True})
        else:
            optlist.update({'reciprocal': False})
        if not len(optlist['from'].split('@')) == 2:
            irc.error(_('--from should be like "--from #channel@network"'))
            return
        if not len(optlist['to'].split('@')) == 2:
            irc.error(_('--to should be like "--to #channel@network"'))
            return
        return optlist

    @internationalizeDocstring
    def add(self, irc, msg, args, optlist):
        """[--from <channel>@<network>] [--to <channel>@<network>] [--regexp <regexp>] [--reciprocal]

        Adds a relay to the list. You must give at least --from or --to; if
        one of them is not given, it defaults to the current channel@network.
        Only messages matching <regexp> will be relayed; if <regexp> is not
        given, everything is relayed.
        If --reciprocal is given, another relay will be added automatically,
        in the opposite direction."""
        optlist = self._parseOptlist(irc, msg, optlist)
        if optlist is None:
            return

        failedWrites = 0
        if not self._writeToConfig(optlist['from'], optlist['to'],
                                   optlist['regexp'], True):
            failedWrites += 1
        if optlist['reciprocal']:
            if not self._writeToConfig(optlist['to'], optlist['from'],
                                       optlist['regexp'], True):
                failedWrites +=1

        self._loadFromConfig()
        if failedWrites == 0:
            irc.replySuccess()
        else:
            irc.error(_('One (or more) relay(s) already exists and has not '
                        'been added.'))
    add = wrap(add, [('checkCapability', 'admin'),
                     getopts({'from': 'something',
                              'to': 'something',
                              'regexp': 'something',
                              'reciprocal': ''})])

    @internationalizeDocstring
    def remove(self, irc, msg, args, optlist):
        """[--from <channel>@<network>] [--to <channel>@<network>] [--regexp <regexp>] [--reciprocal]

        Remove a relay from the list. You must give at least --from or --to; if
        one of them is not given, it defaults to the current channel@network.
        Only messages matching <regexp> will be relayed; if <regexp> is not
        given, everything is relayed.
        If --reciprocal is given, another relay will be removed automatically,
        in the opposite direction."""
        optlist = self._parseOptlist(irc, msg, optlist)
        if optlist is None:
            return

        failedWrites = 0
        if not self._writeToConfig(optlist['from'], optlist['to'],
                                   optlist['regexp'], False):
            failedWrites += 1
        if optlist['reciprocal']:
            if not self._writeToConfig(optlist['to'], optlist['from'],
                                       optlist['regexp'], False):
                failedWrites +=1

        self._loadFromConfig()
        if failedWrites == 0:
            irc.replySuccess()
        else:
            irc.error(_('One (or more) relay(s) did not exist and has not '
                        'been removed.'))
    remove = wrap(remove, [('checkCapability', 'admin'),
                     getopts({'from': 'something',
                              'to': 'something',
                              'regexp': 'something',
                              'reciprocal': ''})])

    def _getSubstitutes(self):
        # Get a list of strings
        substitutes = self.registryValue('substitutes').split(' || ')
        if substitutes == ['']:
            return {}
        # Convert it to a list of tuples
        substitutes = [tuple(x.split(' | ')) for x in substitutes]
        # Finally, make a dictionnary
        substitutes = dict(substitutes)

        return substitutes

    def _setSubstitutes(self, substitutes):
        # Get a list of tuples from the dictionnary
        substitutes = substitutes.items()
        # Make it a list of strings
        substitutes = ['%s | %s' % (x,y) for x,y in substitutes]
        # Finally, get a string
        substitutes = ' || '.join(substitutes)

        self.setRegistryValue('substitutes', value=substitutes)


    @internationalizeDocstring
    def substitute(self, irc, msg, args, regexp, to):
        """<regexp> <replacement>

        Replaces all nicks that matches the <regexp> by the <replacement>
        string."""
        substitutes = self._getSubstitutes()
        # Don't check if it is already in the config: if will be overriden
        # automatically and that is a good thing.
        substitutes.update({regexp: to})
        self._setSubstitutes(substitutes)
        self._loadFromConfig()
        irc.replySuccess()
    substitute = wrap(substitute, [('checkCapability', 'admin'),
                                   'something',
                                   'text'])

    @internationalizeDocstring
    def nosubstitute(self, irc, msg, args, regexp):
        """<regexp>

        Undo a substitution."""
        substitutes = self._getSubstitutes()
        if regexp not in substitutes:
            irc.error(_('This regexp was not in the nick substitutions '
                        'database'))
            return
        # Don't check if it is already in the config: if will be overriden
        # automatically and that is a good thing.
        substitutes.pop(regexp)
        self._setSubstitutes(substitutes)
        self._loadFromConfig()
        irc.replySuccess()
    nosubstitute = wrap(nosubstitute, [('checkCapability', 'admin'),
                                       'something'])



Class = LinkRelay

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
