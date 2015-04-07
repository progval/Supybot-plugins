# -*- coding: utf8 -*-
###
# Copyright (c) 2013, Valentin Lorentz
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

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NoisyKarma')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class NoisyKarma(callbacks.Plugin):
    """Add the help for "@plugin help NoisyKarma" here
    This should describe *how* to use this plugin."""

    def doPrivmsg(self, irc, msg):
        Karma = irc.getCallback('Karma')
        channel = msg.args[0]
        regexp = re.compile(r'[  ,;&|\\.:/?!]')
        if Karma and not msg.addressed and not msg.repliedTo and \
                irc.isChannel(channel):
            (L, neutrals) = Karma.db.gets(channel, regexp.split(msg.args[1]))
            if not L:
                return
            (thing, karma) = L[0] if abs(L[0][1]) > abs(L[-1][1]) else L[-1]
            if karma > 0:
                registry_value = conf.supybot.plugins.NoisyKarma.messages.positive
            elif karma < 0:
                registry_value = conf.supybot.plugins.NoisyKarma.messages.negative
                karma = -karma
            else:
                return
            registry_value = registry_value.get(channel)
            last_key = 0
            last_value = None
            for key, value in sorted(registry_value().items(), key=lambda x:x[0]):
                if int(key) > karma:
                    break
                (last_key, last_value) = (key, value)
            if last_key == 0:
                return
            msg = last_value['message']
            try:
                msg %= thing
            except TypeError:
                pass
            irc.reply(msg, action=last_value['action'], prefixNick=False)

    @wrap(['channel', 'int', getopts({'action': ''}), 'text'])
    def add(self, irc, msg, args, channel, karma, tuple_optlist, message):
        """[<channel>] <min karma> [--action] <msg>

        Adds a new <msg> to be triggered when a thing with a positive
        (respectively negative) karma greater than (resp. lower than)
        <min karma> is saw on the <channel>."""
        optlist = {}
        for key, value in tuple_optlist:
            optlist.update({key: value})
        if karma > 0:
            registry_value = conf.supybot.plugins.NoisyKarma.messages.positive
        elif karma < 0:
            registry_value = conf.supybot.plugins.NoisyKarma.messages.negative
            karma = -karma
        else:
            irc.error(_('Karma cannot be null.', Raise=True))
        registry_value = registry_value.get(channel)
        with registry_value.editable() as rv:
            if str(karma) in rv:
                # Why do we need this????
                del rv[str(karma)]
            rv[karma] = {'action': 'action' in optlist, 'message': message}
        irc.replySuccess()

    @wrap(['channel', 'int'])
    def remove(self, irc, msg, args, channel, tuple_optlist, karma):
        """[<channel>] <min karma>

        Removes the message associated with <thing> and <min karma>."""
        optlist = {}
        for key, value in tuple_optlist:
            optlist.update({key: value})
        if karma > 0:
            registry_value = conf.supybot.plugins.NoisyKarma.messages.positive
        elif karma < 0:
            registry_value = conf.supybot.plugins.NoisyKarma.messages.negative
            karma = -karma
        else:
            irc.error(_('Karma cannot be null.', Raise=True))
        registry_value = registry_value.get(channel)
        with registry_value.editable() as rv:
            del rv[karma]
        irc.replySuccess()

    @wrap(['channel', optional('int')])
    def list(self, irc, msg, args, channel, minimum):
        """[<channel>] [<minimum>]

        Returns the list of messages for karma >=minimum (in absolute
        value)."""
        minimum = minimum or 0
        if minimum > 0:
            val = self.registryValue('messages.positive', channel)
            val = [(int(x), y) for (x,y) in val.items()]
            val = sorted(val, key=lambda x:x[0])
        elif minimum < 0:
            val = self.registryValue('messages.negative', channel)
            val = [(-int(x), y) for (x,y) in val.items()]
            val = sorted(val, key=lambda x:abs(x[0]))
        else:
            pos = self.registryValue('messages.positive', channel)
            pos = [(int(x), y) for (x,y) in pos.items()]
            neg = self.registryValue('messages.negative', channel)
            neg = [(-int(x), y) for (x,y) in neg.items()]
            val = pos + neg
            val = sorted(val, key=lambda x:x[0])
        L = [_('%d: %s (action: %r)') % (karma, message['message'], message['action'])
             for (karma, message) in val
             if abs(karma) >= abs(minimum)]
        irc.reply(format('%L', L))


Class = NoisyKarma


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
