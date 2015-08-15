###
# Copyright (c) 2014, Valentin Lorentz
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
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('IgnoreNonVoice')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class IgnoreNonVoice(callbacks.Plugin):
    """Add the help for "@plugin help IgnoreNonVoice" here
    This should describe *how* to use this plugin."""
    def __init__(self, irc):
        super(IgnoreNonVoice, self).__init__(irc)
        callbacks.Commands.pre_command_callbacks.append(
                self._pre_command_callback)

    def die(self):
        callbacks.Commands.pre_command_callbacks.remove(
                self._pre_command_callback)

    def _is_not_ignored(self, irc, msg):
        channel = msg.args[0]
        if not ircutils.isChannel(channel) or \
                channel not in irc.state.channels:
            return False
        enabled = self.registryValue('enable', channel) or \
                (self.registryValue('enableIfModerated', channel) and \
                'm' in irc.state.channels[channel].modes)
        return enabled and \
                not irc.state.channels[channel].isVoicePlus(msg.nick)
    def _pre_command_callback(self, plugin, command, irc, msg, *args, **kwargs):
        return self._is_not_ignored(irc, msg)

    def invalidCommand(self, irc, msg, tokens):
        if not self._is_not_ignored(irc, msg):
            irc.noReply()


Class = IgnoreNonVoice


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
