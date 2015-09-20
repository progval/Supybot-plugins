# -*- Encoding: utf-8 -*-
###
# Copyright (c) 2008-2010 Terence Simpson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
import supybot.ircutils as ircutils
import supybot.ircdb as ircdb
import supybot.conf as conf
import os
import re
import time
import packages
reload(packages)

def get_user(msg):
    try:
        user = ircdb.users.getUser(msg.prefix)
    except:
        return False
    return user

_stripNickChars = """!"#$%&'()*+,./:;<=>?@~"""
def stripNick(nick):
    while nick and nick[-1] in _stripNickChars:
        nick = nick[:-1]
    return nick

## Taken from Encyclopedia ##
# Repeat filtering message queue
msgcache = {}
def queue(irc, to, msg):
    now = time.time()
    for m in msgcache.keys():
        if msgcache[m] < now - 30:
            msgcache.pop(m)
    for m in msgcache:
        if m[0] == irc and m[1] == to:
            oldmsg = m[2]
            if msg == oldmsg or oldmsg.endswith(msg):
                break
            if msg.endswith(oldmsg):
                msg = msg[:-len(oldmsg)] + 'please see above'
    else:
        msgcache[(irc, to, msg)] = now
        irc.queueMsg(ircmsgs.privmsg(to, msg))

class PackageInfo(callbacks.Plugin):
    """Lookup package information via apt-cache/apt-file"""
    threaded = True
    space_re = re.compile(r'  *')

    def __init__(self, irc):
        self.__parent = super(PackageInfo, self)
        self.__parent.__init__(irc)
        self.Apt = packages.Apt(self)

    def callPrecedence(self, irc):
        before = []
        for cb in irc.callbacks:
            if cb.name() == 'IRCLogin':
                before.append(cb)
        return (before, [])

    def __getRelease(self, irc, release, channel, doError=True):
        if release:
            release = release.strip()
        defaultRelease = self.registryValue("defaultRelease", channel)
        if not defaultRelease:
            if doError:
                irc.error("'supybot.plugins.PackageInfo.defaultRelease' is not set")
            return (None, None)
        if not release:
            return (defaultRelease, None)
        (release, rest) = (release.split(' ', 1) + [None])[:2]
        if release[0] in ('|', '>'):
            return (defaultRelease, "%s %s" % (release, rest))
        return (release, rest)

    def __getChannel(self, channel):
        return ircutils.isChannel(channel) and channel or None

    def __getReplyChars(self, channel):
        prefix_chars = list(self.registryValue("prefixchar", channel))
        address_chars = list(str( conf.supybot.reply.whenAddressedBy.chars() ))
        if channel:
            address_chars = list(str( conf.supybot.reply.whenAddressedBy.chars.get(channel) ))
        return tuple(set(prefix_chars + address_chars))

    def __getCommand(self, text, channel):
        reply_chars = self.__getReplyChars(channel)
        my_commands = self.listCommands()
        if text[0] in reply_chars:
            text = text[1:]
        return text.strip().lower().split(' ', 1)[0]

    def real_info(self, irc, msg, args, package, release):
        """<package> [<release>]

        Lookup information for <package>, optionally in <release>
        """
        channel = self.__getChannel(msg.args[0])
        reply_target = ircutils.replyTo(msg)
        (release, rest) = self.__getRelease(irc, release, channel)
        if not release:
            return
        reply = self.Apt.info(package, release)
        if rest:
            if rest[0] == '|':
                try:
                    target = rest
                    while target[0] == '|':
                        target = target[1:].strip()
                    if target.lower() == "me":
                        target = msg.nick
                    queue(irc, reply_target, "%s: %s" % (target, reply))
                    return
                except Exception, e:
                    self.log.info("PackageInfo: (info) Exception in pipe: %r" % e)
                    pass
            elif rest[0] == '>':
                try:
                    while rest[0] == '>':
                        rest = rest[1:].strip()
                    targets = [_ for _ in rest.split() if _] # Split and discard empty parts
                    target = stripNick(targets[0]) # Take the first "nick" and strip off bad chars
                    if target.lower() == "me":
                        target = msg.nick # redirect
                    if not target: # Throw error
                        raise Exception, 'No target'
                    queue(irc, target, "<%s> wants you to know: %s" % (msg.nick, reply))
                    return
                except Exception, e:
                    self.log.info("PackageInfo: (info) Exception in redirect: %r" % e)
                    pass

        queue(irc, reply_target, reply)

    info = wrap(real_info, ['anything', optional('text')])

    def real_find(self, irc, msg, args, package, release):
        """<package/filename> [<release>]

        Search for <package> or, of that fails, find <filename>'s package(s).
        Optionally in <release>
        """
        channel = self.__getChannel(msg.args[0])
        reply_target = ircutils.replyTo(msg)
        (release, rest) = self.__getRelease(irc, release, channel)
        if not release:
            return
        reply = self.Apt.find(package, release)
        if rest:
            if rest[0] == '|':
                try:
                    target = rest
                    while target[0] == '|':
                        target = target[1:].strip()
                    if target.lower() == "me":
                        target = msg.nick
                    queue(irc, reply_target, "%s: %s" % (target, reply))
                    return
                except Exception, e:
                    self.log.info("PackageInfo: (find) Exception in pipe: %r" % e)
                    pass
            elif rest[0] == '>':
                try:
                    while rest[0] == '>':
                        rest = rest[1:].strip()
                    targets = [_ for _ in rest.split() if _] # Split and discard empty parts
                    target = stripNick(targets[0]) # Take the first "nick" and strip off bad chars
                    if target.lower() == "me":
                        target = msg.nick # redirect
                    if not target: # Throw error
                        raise Exception, 'No target'
                    queue(irc, target, "<%s> wants you to know: %s" % (msg.nick, reply))
                    return
                except Exception, e:
                    self.log.info("PackageInfo: (find) Exception in redirect: %r" % e)
                    pass

        queue(irc, reply_target, reply)

    find = wrap(real_find, ['anything', optional('text')])

    def privmsg(self, irc, msg, user):
        channel = self.__getChannel(msg.args[0])
        text = self.space_re.subn(' ', msg.args[1].strip())[0]
        my_commands = self.listCommands()
        if text[0] == self.registryValue("prefixchar"):
            text = text[1:].strip()
        if user and text[0] in list(conf.supybot.reply.whenAddressedBy.chars()):
            return
        (cmd, rest) = (text.split(' ', 1) + [None])[:2]
        if cmd not in my_commands:
            return
        if not rest:
            return
        (term, rest) = (rest.split(' ', 1) + [None])[:2]
        if cmd == "find":
            self.real_find(irc, msg, [], term, rest)
        else:
            self.real_info(irc, msg, [], term, rest)

    def chanmsg(self, irc, msg, user):
        channel = self.__getChannel(msg.args[0])
        text = self.space_re.subn(' ', msg.args[1].strip())[0]
        my_commands = self.listCommands()
        if text[0] != self.registryValue("prefixchar", channel):
            return
        text = text[1:]
        (cmd, rest) = (text.split(' ', 1) + [None])[:2]
        if cmd not in my_commands:
            return
        if not rest:
            return
        (term, rest) = (rest.split(' ', 1) + [None])[:2]
        if cmd == "find":
            self.real_find(irc, msg, [], term, rest)
        else:
            self.real_info(irc, msg, [], term, rest)

    def doPrivmsg(self, irc, msg):
        if chr(1) in msg.args[1]: # CTCP
            return
        if not msg.args[1]:
            return
        channel = self.__getChannel(msg.args[0])
        if not self.registryValue("enabled", channel):
            return
        user = get_user(msg)
        if channel:
            self.chanmsg(irc, msg, user)
        else:
            if user:
                return
            self.privmsg(irc, msg, user)

    def inFilter(self, irc, msg):
        if msg.command != "PRIVMSG":
            return msg
        if not conf.supybot.defaultIgnore():
            return msg
        text = msg.args[1].strip()
        if len(text) < 6:
            return msg
        user = get_user(msg)
        channel = self.__getChannel(msg.args[0])
        reply_chars = self.__getReplyChars(channel)
        my_commands = self.listCommands()
        cmd = self.__getCommand(text, channel)

        if cmd not in my_commands:
            return msg

        if user:
            if not channel and text[0] == self.registryValue("prefixchar"):
                msg.args = (msg.args[0], text[1:])
            return msg

        if channel:
            if text[0] not in reply_chars:
                return msg

#            if not hasattr(irc, 'reply'):
#                irc = callbacks.ReplyIrcProxy(irc, msg)
#            self.doPrivmsg(irc, msg)
        else:
            if text[1] in reply_chars:
                msg.args = (msg.args[0], text[1:])
            irc = callbacks.ReplyIrcProxy(irc, msg)
            self.doPrivmsg(irc, msg)

        return msg

Class = PackageInfo


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
