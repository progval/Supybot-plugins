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

import time
import chardet
import supybot.log as log
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('NoLatin1')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

@internationalizeDocstring
class NoLatin1(callbacks.Plugin):
    """Add the help for "@plugin help NoLatin1" here
    This should describe *how* to use this plugin."""

    _warnings = {}

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        content = msg.args[1]
        if not self.registryValue('enable', channel):
            return
        encoding = chardet.detect(content)['encoding']
        if encoding not in ('utf-8', 'ascii'):
            log.info('Warning %s (using %s)' % (msg.prefix, encoding))
            self._warn(irc, channel, msg.prefix.split('!')[0])

    def _warn(self, irc, channel, nick):
        id_ = '%s@%s' % (nick, channel)
        if id_ in self._warnings:
            warnLevel = self._warnings[id_]
            remember = self.registryValue('remember',channel)
            if warnLevel[0] < time.time() - remember:
                warnLevel = 1 # Reset to 0 + 1
            else:
                warnLevel = warnLevel[1] + 1
        else:
            warnLevel = 1
        self._warnings.update({id_: (time.time(), warnLevel)})
        maxWarningsBeforeAlert = self.registryValue('maxWarningsBeforeAlert')
        operator = self.registryValue('operator')
        if warnLevel >= maxWarningsBeforeAlert:
            irc.reply(_('User %s is still using Latin-1 after %i alerts') %
                      (nick, maxWarningsBeforeAlert), private=True, to=operator)
            warnLevel = 0
        else:
            irc.reply(_('Please use Unicode/UTF-8 instead of '
                        'Latin1/ISO-8859-1 on %s.') % channel,
                      private=True)
        self._warnings.update({id_: (time.time(), warnLevel)})



Class = NoLatin1


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
