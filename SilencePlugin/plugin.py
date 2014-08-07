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

import sys

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('SilencePlugin')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

if not hasattr(callbacks.Commands, 'pre_command_callbacks'):
    raise callbacks.Error(
            'Your version of Supybot is not compatible with '
            'this plugin (it does not have support for '
            'pre-command-call callbacks).')

plugin_class_name_tag = 'SilencePlugin__originated_from'
class IrcMsg(ircmsgs.IrcMsg):
    def __init__(self2, *args, **kwargs):
        super(IrcMsg, self2).__init__(*args, **kwargs)
        plugin = None
        f = sys._getframe().f_back
        while f:
            if 'irc' in f.f_locals and \
                    isinstance(f.f_locals['self'], callbacks.Commands):
                plugin = f.f_locals['self']
                break
            f = f.f_back
        if plugin:
            self2.tag(plugin_class_name_tag, plugin.name())

class SilencePlugin(callbacks.Plugin):
    """Add the help for "@plugin help SilencePlugin" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        super(SilencePlugin, self).__init__(irc)
        callbacks.Commands.pre_command_callbacks.append(
                self._pre_command_callback)
        self._original_ircmsg = ircmsgs.IrcMsg
        ircmsgs.IrcMsg = IrcMsg

    def die(self):
        callbacks.Commands.pre_command_callbacks.remove(
                self._pre_command_callback)
        ircmsgs.IrcMsg = self._original_ircmsg

    def _pre_command_callback(self, plugin, command, irc, msg, *args, **kwargs):
        return plugin in self.registryValue('inblacklist')

    def outFilter(self, irc, msg):
        plugin = None
        if msg.tagged(plugin_class_name_tag):
            plugin = msg.tagged(plugin_class_name_tag)
        else:
            self.log.warning('Message from no plugin: %r', msg)
            return msg
        if plugin in self.registryValue('outblacklist'):
            return None
        else:
            return msg
    def inFilter(self, irc, msg):
        return msg



Class = SilencePlugin


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
