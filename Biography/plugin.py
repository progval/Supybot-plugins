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

import supybot.conf as conf
import supybot.world as world
import supybot.utils as utils
import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Biography')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x


class BiographyDB(plugins.ChannelUserDB):
    def serialize(self, v):
        return [v]

    def deserialize(self, channel, id, L):
        if len(L) != 1:
            raise ValueError
        return L[0]

@internationalizeDocstring
class Biography(callbacks.Plugin):
    """Add the help for "@plugin help Biography" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        super(Biography, self).__init__(irc)

        filename = conf.supybot.directories.data.dirize('Biography.db')
        self.db = BiographyDB(filename)
        world.flushers.append(self.db.flush)

    def die(self):
        if self.db.flush in world.flushers:
            world.flushers.remove(self.db.flush)
        self.db.close()
        super(Biography, self).die()

    def _preCheck(self, irc, msg, user):
        # Stolen from Herald plugin
        capability = self.registryValue('requireCapability')
        if capability:
            try:
                u = ircdb.users.getUser(msg.prefix)
            except KeyError:
                irc.errorNotRegistered(Raise=True)
            else:
                if u != user:
                    if not ircdb.checkCapability(msg.prefix, capability):
                        irc.errorNoCapability(capability, Raise=True)

    @internationalizeDocstring
    def get(self, irc, msg, args, channel, user, key):
        """[<channel>] [<username>] [<field>]

        Gets an information for the <username>. If <field> is not given, all
        informations are returned."""
        fields = self.registryValue('fields', channel)
        if key and key not in fields:
            s = format(_('This is not a valid field. Valid fields are: %L'),
                    fields)
            irc.error(s, Raise=True)
        channeluser = (channel, user.id)
        if channeluser not in self.db:
            irc.error(_('No information on this user.'), Raise=True)
        info = self.db[channeluser]
        if key:
            if key not in info:
                irc.error(_('Information not available for this user.'),
                        Raise=True)
            irc.reply(_('%(key)s for %(user)s: %(value)s') % {
                'key': key, 'user': user.name,
                'value': info[key]})
        else:
            def part(key):
                return _('%(key)s: %(value)s') % {
                        'key': ircutils.bold(key),
                        'value': info[key],
                        }
            parts = map(lambda x:part(x) if x in info else '', fields)
            irc.reply(format('%L', parts))
    get = wrap(get, ['channel', first('otherUser', 'user'),
        optional('something')])

    @internationalizeDocstring
    def set(self, irc, msg, args, channel, user, key, value):
        """[<channel>] [<username>] <field> <value>

        Sets an information for the <username>."""
        self._preCheck(irc, msg, user)
        fields = self.registryValue('fields', channel)
        if key not in fields:
            s = format(_('This is not a valid field. Valid fields are: %L'),
                    fields)
            irc.error(s, Raise=True)
        channeluser = (channel, user.id)
        if channeluser not in self.db:
            self.db[channeluser] = {}
        self.db[channeluser].update({key: value})
        irc.replySuccess()
    set = wrap(set, ['channel', first('otherUser', 'user'),
        'something', 'text'])


Class = Biography


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
