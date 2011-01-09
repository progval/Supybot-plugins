###
# Copyright (c) 2010, quantumlemur
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
import string
import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.irclib as irclib
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
#from supybot.utils.structures import MultiSet, TimeoutQueue

class LinkRelay(callbacks.Plugin):
    noIgnore = True
    threaded = True
    
    # Put a list of all the relays that you want to add here.  Only messages
    # matching the regex will be relayed. 
    # syntax is [sourceChannel, sourceNetwork, targetChannel, targetNetwork, regex]
    relaysToAdd = [
            #['#supybot', 'freenode', '#supybot-bots', 'freenode', ''],
            #['#supybot-bots', 'freenode', '#supybot', 'freenode', '']
            ]
     
    # include any nick substitutions that you want to make here
    # (for example, if a user is in both channels, and doesn't want to get
    # highlighted every time they say a message)
    nickSubstitutions = {
            #'quantumlemur': 'quantu*lemu*'
            }


    class Relay():
        def __init__(self, sourceChannel, sourceNetwork, targetChannel, targetNetwork, channelRegex, networkRegex, messageRegex):
            self.sourceChannel = sourceChannel
            self.sourceNetwork = sourceNetwork
            self.targetChannel = targetChannel
            self.targetNetwork = targetNetwork
            self.channelRegex = channelRegex
            self.networkRegex = networkRegex
            self.messageRegex = messageRegex
            self.hasIRC = False


    def __init__(self, irc):
        self.__parent = super(LinkRelay, self)
        self.__parent.__init__(irc)
        self.relays = []
        for relay in self.relaysToAdd:
            self.relays.append(self.Relay(relay[0], relay[1], relay[2], relay[3], re.compile('^%s$' % relay[0], re.I), re.compile('^%s$' % relay[1]), re.compile(relay[4])))
        for IRC in world.ircs:
            self.addIRC(IRC)


    def simpleHash(self, s):
        colors = ["\x0305", "\x0304", "\x0303", "\x0309", "\x0302", "\x0312", "\x0306",   "\x0313", "\x0310", "\x0311", "\x0307"]
        num = 0
        for i in s:
            num += ord(i)
        num = num % 11
        if s == 'xen':
            num = 5
        elif s == 'splurk':
            num = 5
        return colors[num]


    def formatPrivMsg(self, nick, text):
        color = self.simpleHash(nick)
        if nick in self.nickSubstitutions:
            nick = self.nickSubstitutions[nick]
        if re.match('^\x01ACTION .*\x01$', text):
            text = text.strip('\x01')
            text = text[ 7 : ]
            s = '\x0314*\x03 %s %s' % (nick, text)
        else:
            s = '\x0314<%s%s\x0314>\x03 %s' % (color, nick, text)
        return s


    def list(self, irc, msg, args):
        """takes no arguments

        Returns all the defined relay links"""
        for relay in self.relays:
            if relay.hasIRC:
                hasIRC = 'Link healthy!'
            else:
                hasIRC = '\x0304IRC object not scraped yet.\x03'
            irc.sendMsg(ircmsgs.privmsg(msg.args[0], '\x02%s\x02 on \x02%s\x02   ==>   \x02%s\x02 on \x02%s\x02.  %s' % (relay.sourceChannel, relay.sourceNetwork, relay.targetChannel, relay.targetNetwork, hasIRC)))

    def doPrivmsg(self, irc, msg):
        self.addIRC(irc)
        s = self.formatPrivMsg(msg.nick, msg.args[1])
        self.sendToOthers(irc, msg, s)


    def outFilter(self, irc, msg):
        if msg.command == 'PRIVMSG':
            if not msg.relayedMsg:
                if msg.args[0] in irc.state.channels:
                    s = self.formatPrivMsg(irc.nick, msg.args[1])
                    self.sendToOthers(irc, msg, s)
        return msg
   

    def doPing(self, irc, msg):
        self.addIRC(irc)

    def doJoin(self, irc, msg):
        s = '\x0314%s has joined on %s' % (msg.nick, irc.network)
        self.sendToOthers(irc, msg, s)

    def doPart(self, irc, msg):
        s = '\x0314%s has left on %s' % (msg.nick, irc.network)
        self.sendToOthers(irc, msg, s)

#    def doQuit(self, irc, msg):
#        for channel in self.ircstates[irc].channels:
#            if msg.nick in self.ircstates[irc].channels[channel].users:
#                s = '\x0314%s has quit on %s (%s)' % (msg.nick, irc.network, msg.args[0])
#                m = msg
#                self.sendToOthers(irc, msg, s)

    def doKick(self, irc, msg):
        s = '\x0314%s has been kicked on %s by %s (%s)' % (msg.args[1], irc.network, msg.nick, msg.args[2])
        self.sendToOthers(irc, msg, s)

    def sendToOthers(self, irc, triggerMsg, s):
        channel = triggerMsg.args[0]
        nick = triggerMsg.nick
        for relay in self.relays:
            if relay.channelRegex.match(channel) and relay.networkRegex.match(irc.network) and (len(triggerMsg.args[1] < 1 or relay.messageRegex.search(triggerMsg.args[1]))):
                if not relay.hasIRC:
                    self.log.info('LinkRelay:  IRC %s not yet scraped.' % relay.targetNetwork)
                elif relay.targetIRC.zombie:
                    self.log.info('LinkRelay:  IRC %s appears to be a zombie' % relay.targetNetwork)
                elif relay.targetChannel not in relay.targetIRC.state.channels:
                    self.log.info('LinkRelay:  I\'m not in in %s on %s' % (relay.targetChannel, relay.targetNetwork))
                else:
#                    if re.match('\x0314\w+ has quit on \w+ \(.*\)', s):
#                        pm = False
#                    else:
#                        pm = True
#                    for chan in irc.state.channels:
#                        if re.match('^%s$' % relay.sourceChannel, chan):
#                            pm = False
                    if triggerMsg.args[0] not in irc.state.channels and not re.match('\x0314\w+ has quit on \w+ \(.*\)', s):
                        # cuts off the end of commands, so that passwords won't be revealed in relayed PM's
                        if callbacks.addressed(irc.nick, triggerMsg):
                            s = re.sub('(>\x03 \w+) .*', '\\1 \x0314[truncated]', s)
                        s = '(via PM) %s' % s
                    msg = ircmsgs.privmsg(relay.targetChannel, s)
                    msg.tag('relayedMsg')
                    relay.targetIRC.sendMsg(msg)


    def addIRC(self, irc):
        match = False
        for relay in self.relays:
            if relay.targetNetwork == irc.network and not relay.hasIRC:
                relay.targetIRC = irc
                relay.hasIRC = True


    def nicks(self, irc, msg, args, channel):
        """[<channel>]

        Returns the nicks of the people in the linked channels.
        <channel> is only necessary if the message
        isn't sent on the channel itself."""
        for relay in self.relays:
            if relay.targetChannel == channel and relay.targetNetwork == irc.network:
                if not relay.hasIRC:
                    irc.reply('I haven\'t scraped the IRC object for %s yet.  Try again in a minute or two.' % relay.targetNetwork)
                else:
                    users = []
                    ops = []
                    halfops = []
                    voices = []
                    normals = []
                    numUsers = 0
                    try:
                        Channel = relay.targetIRC.state.channels[relay.sourceChannel] #need to do something about this -- right now it won't match a regex channel
                    except KeyError:
                        continue
                    for s in Channel.users:
                        s = s.strip()
                        if not s:
                            continue
                        numUsers += 1
                        if s in Channel.ops:
                            users.append('@%s' % s)
                        elif s in Channel.halfops:
                            users.append('%%%s' % s)
                        elif s in Channel.voices:
                            users.append('+%s' % s)
                        else:
                            users.append(s)
                    #utils.sortBy(ircutils.toLower, ops)
                    #utils.sortBy(ircutils.toLower, halfops)
                    #utils.sortBy(ircutils.toLower, voices)
                    #utils.sortBy(ircutils.toLower, normals)
                    users.sort()
                    msg.tag('relayedMsg')
                    s = '%d users in %s on %s:  %s' % (numUsers, relay.sourceChannel, relay.sourceNetwork, utils.str.commaAndify(users))
                    irc.queueMsg(ircmsgs.privmsg(msg.args[0], s))
        irc.noReply()
    nicks = wrap(nicks, ['Channel'])


Class = LinkRelay

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
