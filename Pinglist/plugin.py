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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Pinglist')

@internationalizeDocstring
class Pinglist(callbacks.Plugin):
    """Add the help for "@plugin help Pinglist" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        super(Pinglist, self).__init__(irc)
        self._subscriptions = ircutils.IrcDict()

    @internationalizeDocstring 
    def pingall(self, irc, msg, args, channel, meeting):
        """[<channel>] <meeting>

        Ping all participants of the <meeting>.
        <channel> defaults to the current channel."""
        try:
            subscribers = self._subscriptions[channel][meeting]
        except KeyError:
            irc.error(_('No such meeting.'), Raise=True)
        if subscribers:
            irc.reply(format(_('Ping %L'), list(subscribers)))
        else:
            # Should not happen
            irc.error(_('No subscribers.'))
    pingall = wrap(pingall, ['channel', 'something'])

    @internationalizeDocstring
    def subscribe(self, irc, msg, args, channel, meeting):
        """[<channel>] <meeting>

        Subscribe to the <meeting>.
        <channel> defaults to the current channel."""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = ircutils.IrcDict()
        if meeting not in self._subscriptions[channel]:
            self._subscriptions[channel][meeting] = ircutils.IrcSet()
        self._subscriptions[channel][meeting].add(msg.nick)
        irc.replySuccess()
    subscribe = wrap(subscribe, ['channel', 'something'])

    @internationalizeDocstring
    def unsubscribe(self, irc, msg, args, channel, meeting):
        """[<channel>] <meeting>

        Unsubscribe from the <meeting>.
        <channel> defaults to the current channel."""
        if channel not in self._subscriptions:
            irc.error(_('No such meeting.'))
        if meeting not in self._subscriptions[channel]:
            irc.error(_('No such meeting.'))
        try:
            self._subscriptions[channel][meeting].remove(msg.nick)
        except KeyError:
            irc.error(_('You did not subscribe.'), Raise=True)
        if not self._subscriptions[channel][meeting]:
            del self._subscriptions[channel][meeting]
        if not self._subscriptions[channel]:
            del self._subscriptions[channel]
        irc.replySuccess()
    unsubscribe = wrap(unsubscribe, ['channel', 'something'])





Class = Pinglist


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
