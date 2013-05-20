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
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Rbls')
except:
    # These are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x

class Rbls(callbacks.Plugin):
    """Add the help for "@plugin help Rbls" here
    This should describe *how* to use this plugin."""
    threaded = True

    def doJoin(self, irc, msg):
        channel = msg.args[0]
        if not self.registryValue('enable', channel):
            return
        nick, ident, host = ircutils.splitHostmask(msg.prefix)

        fd = utils.web.getUrlFd('http://rbls.org/%s' % host)
        line = ' '
        while line and not line.startswith('<title>'):
            line = fd.readline()
        if not line:
            return
        if 'is listed in' in line:
            irc.queueMsg(ircmsgs.ban(channel, '*!*@%s' % host))
            irc.queueMsg(ircmsgs.kick(channel, nick))
        else:
            assert 'is not listed' in line



Class = Rbls


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
