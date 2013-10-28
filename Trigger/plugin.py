###
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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Trigger')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x


@internationalizeDocstring
class Trigger(callbacks.Plugin):
    """Add the help for "@plugin help Trigger" here
    This should describe *how* to use this plugin."""
    def __init__(self, irc):
        super(Trigger, self).__init__(irc)
        self.lastMsgs = {}
        self.lastStates = {}
    def __call__(self, irc, msg):
        try:
            super(Trigger, self).__call__(irc, msg)
            if irc in self.lastMsgs:
                if irc not in self.lastStates:
                    self.lastStates[irc] = irc.state.copy()
                self.lastStates[irc].addMsg(irc, self.lastMsgs[irc])
        finally:
            # We must make sure this always gets updated.
            self.lastMsgs[irc] = msg
    def _run(self, irc, msg, triggerName, channel=None):
        if channel is None:
            channel = msg.args[0]
        command = self.registryValue('triggers.%s' % triggerName, channel)
        if not list(filter(lambda x:x!=' ', command)):
            return
        tokens = callbacks.tokenize(command)
        if not tokens:
            return
        try:
            msg.args = (channel,) + msg.args[1:]
            self.Proxy(irc.irc, msg, tokens)
        except Exception as  e:
            self.log.exception('Error occured while running triggered command:')
    def doJoin(self, irc, msg):
        self._run(irc, msg, 'join')
    def doPart(self, irc, msg):
        self._run(irc, msg, 'part')
    def doKick(self, irc, msg):
        self._run(irc, msg, 'kick')
    def doPrivmsg(self, irc, msg):
        self._run(irc, msg, 'privmsg')
        if irc.nick in msg.args[1]:
            self._run(irc, msg, 'highlight')
    def doNotice(self, irc, msg):
        self._run(irc, msg, 'notice')
    def doQuit(self, irc, msg):
        for (channel, c) in self.lastStates[irc].channels.items():
            if msg.nick in c.users:
                self._run(irc, msg, 'quit', channel)
    def doNick(self, irc, msg):
        for (channel, c) in irc.state.channels.items():
            if msg.args[0] in c.users:
                self._run(irc, msg, 'nick', channel)
    def do376(self, irc, msg):
        command = self.registryValue('triggers.connect')
        if command != '':
            irc.queueMsg(ircmsgs.IrcMsg(command))


Class = Trigger


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
