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

import json
import operator
try:
    from urllib import quote
except:
    from urllib.request import quote

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('AutoTrans')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class AutoTrans(callbacks.Plugin):
    """Add the help for "@plugin help AutoTrans" here
    This should describe *how* to use this plugin."""
    threaded = True

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        targets = list(map(lambda x:x.split(':'),
            self.registryValue('queries', channel)))
        whitelist = self.registryValue('authorWhitelist', channel)
        if whitelist:
            if all(not ircutils.hostmaskPatternEqual(pattern, msg.prefix)
                   for pattern in whitelist):
                return

        cb = irc.getCallback('Google')
        if targets and cb is None:
            self.log.error('WikiTrans used but Google plugin not loaded.')
            return

        for lang in set(map(operator.itemgetter(1), targets)):
            (text, language) = cb._translate('auto', lang, msg.args[1])
            text = '<%s@%s> %s' % (msg.nick, channel, text)
            for (nick, user_lang) in targets:
                if user_lang != language and user_lang == lang:
                    irc.reply(text, to=nick, private=True, notice=False)


Class = AutoTrans


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
