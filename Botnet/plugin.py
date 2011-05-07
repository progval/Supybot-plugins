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
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Botnet')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x


def botnetWrap(function):
    return wrap(function, [('checkCapability', 'bot'),
                           ('checkCapability', 'trusted'),
                           ('something',),         # version
                           ('something',),         # hashid
                           ('text',)])             # args

@internationalizeDocstring
class Botnet(callbacks.Plugin):
    """Add the help for "@plugin help Botnet" here
    This should describe *how* to use this plugin."""
    threaded = True

    _version = '0.1'

    def _reply(irc, messages, hashid = None):
        assert len(messages) != 0, 'Empty messages list'
        if hashid is None:
            assert len(messages) == 1, ('Queries should not have more than '
                                        'one message.')
            messagesHash = hashlib.sha224(messages).hexdigest()
            hashid = '%i-%s' % (time.time(), messagesHash)
            irc.reply('botnet query %s %s %s' % (self._version, hashid, msg))
        else:
            if len(messages) > 1:
                irc.reply('botnet start %s %s' % (self._version, hashid))
            for message in messages:
                irc.reply('botnet reply %s %s %s' % (self._version,hashid,msg))
            if len(messages) > 1:
                irc.reply('botnet end %s %s' % (self._version, hashid)
        return hashid

    # Not handled by version 0.1
    @botnetWrap
    def start(self, irc, msg, args, version, hashid, text):
        raise NotImplemented()
    end = start

    @botnetWrap
    def reply(self, irc, msg, args, version, hashid, text):
        splitted = text.split(' ')
        assert len(splitted) >= 1
        command, args = splitted[0], ' '.join(splitted[1:])

    @botnetWrap
    def query(self, irc, msg, args, version, hashid, text):
        self._reply(irc, [], hashid)


Class = Botnet


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
