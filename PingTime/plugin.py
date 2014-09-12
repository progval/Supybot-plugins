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

import time

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PingTime')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

# TODO: Make this configurable/internationalizable
triggers_base = r'^((?P<nick>%s)[,:]? %%s|%%s (?P<nick2>%s))$' % \
        ((ircutils.nickRe.pattern[1:-1],)*2)
class PingTime(callbacks.PluginRegexp):
    """Add the help for "@plugin help PingTime" here
    This should describe *how* to use this plugin."""
    regexps = ('onPing', 'onPong')

    _pings = {} # {channel: {(from, to): timestamp}}

    def onPing(self, irc, msg, match):
        channel = msg.args[0]
        from_ = msg.nick
        to = match.group('nick') or match.group('nick2')
        if not (ircutils.isChannel(channel) and self.registryValue('enable',
            msg.args[0])):
            return
        if channel not in self._pings:
            self._pings[channel] = {}
        self._pings[channel][(from_, to)] = time.time()
    onPing.__doc__ = triggers_base % (('ping',)*2)

    def onPong(self, irc, msg, match):
        channel = msg.args[0]
        from_ = msg.nick
        to = match.group('nick') or match.group('nick2')
        if not (ircutils.isChannel(channel) and self.registryValue('enable',
            msg.args[0])):
            return
        try:
            pinged_at = self._pings[channel].pop((to, from_))
        except KeyError:
            return
        else:
            delta = time.time()-pinged_at
            if delta > 1:
                irc.reply(utils.str.format(_('Ping time: %T'), delta))

    onPong.__doc__ = triggers_base % (('pong',)*2)


Class = PingTime


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
