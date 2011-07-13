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

import supybot.conf as conf
import supybot.ircutils as ircutils
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('LinkRelay')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

def configure(advanced):
    from supybot.questions import output, expect, anything, something, yn
    conf.registerPlugin('LinkRelay', True)


class ColorNumber(registry.String):
    """Value must be a valid color number (01, 02, 03, 04, ..., 16)"""
    def set(self, s):
        if s not in ('01', '02', '03', '04', '05', '06', '07', '08', '09',
                     '10', '11', '12', '13', '14', '15', '16'):
            self.error()
            return
        self.setValue(s)
ColorNumber = internationalizeDocstring(ColorNumber)


LinkRelay = conf.registerPlugin('LinkRelay')
conf.registerChannelValue(LinkRelay, 'color',
    registry.Boolean(False, _("""Determines whether the bot will color Relayed
    PRIVMSGs so as to make the messages easier to read.""")))
conf.registerChannelValue(LinkRelay, 'topicSync',
    registry.Boolean(True, _("""Determines whether the bot will synchronize
    topics between networks in the channels it Relays.""")))
conf.registerChannelValue(LinkRelay, 'hostmasks',
    registry.Boolean(False, _("""Determines whether the bot will Relay the
    hostmask of the person joining or parting the channel when he or she joins
    or parts.""")))
conf.registerChannelValue(LinkRelay, 'includeNetwork',
    registry.Boolean(True, _("""Determines whether the bot will include the
    network in Relayed PRIVMSGs; if you're only Relaying between two networks,
    it's somewhat redundant, and you may wish to save the space.""")))

class ValidNonPrivmsgsHandling(registry.OnlySomeStrings):
    validStrings = ('privmsg', 'notice', 'nothing')
conf.registerChannelValue(LinkRelay, 'nonPrivmsgs',
    ValidNonPrivmsgsHandling('privmsg', _("""Determines whether the
    bot will use PRIVMSGs (privmsg), NOTICEs (notice), for non-PRIVMSG Relay
    messages (i.e., joins, parts, nicks, quits, modes, etc.), or whether it
    won't relay such messages (nothing)""")))

conf.registerGlobalValue(LinkRelay, 'relays',
    registry.String('', _("""You shouldn't edit this configuration variable
    yourself unless you know what you do. Use @LinkRelay {add|remove} instead.""")))

conf.registerGlobalValue(LinkRelay, 'substitutes',
    registry.String('', _("""You shouldn't edit this configuration variable
    yourself unless you know what you do. Use @LinkRelay (no)substitute instead.""")))

conf.registerGroup(LinkRelay, 'colors')
for name, color in {'info': '02',
                    'truncated': '14',
                    'mode': '14',
                    'join': '14',
                    'part': '14',
                    'kick': '14',
                    'nick': '14',
                    'quit': '14'}.items():
    conf.registerChannelValue(LinkRelay.colors, name,
        ColorNumber(color, _("""Color used for relaying %s.""") % color))


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
