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

import re

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Coinpan')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

_regexp = re.compile('c[o0][i1]n', re.I)
def replacer(match):
    coin = match.group(0)
    assert len(coin) == 4
    pan = ''
    if coin[0] == 'c':
        pan += 'p'
    elif coin[0] == 'C':
        pan += 'P'
    else:
        raise AssertionError(coin)
    if coin[1] == '0' or coin[2] == '1':
        pan += '4'
    elif coin[1] == 'O' or coin[2] == 'I':
        pan += 'A'
    elif coin[1] == 'o' and coin[2] == 'i':
        pan += 'a'
    else:
        raise AssertionError(coin)
    if coin[3] == 'n':
        pan += 'n'
    elif coin[3] == 'N':
        pan += 'N'
    else:
        raise AssertionError(coin)
    return pan

class Coinpan(callbacks.PluginRegexp):
    """Add the help for "@plugin help Coinpan" here
    This should describe *how* to use this plugin."""

    regexps = ['coinSnarfer']

    @urlSnarfer
    def coinSnarfer(self, irc, msg, match):
        """(?i).*c[o0][i1]n.*"""
        if self.registryValue('enable', msg.args[0]):
            irc.reply(_regexp.sub(replacer, msg.args[1]), prefixNick=False)


Class = Coinpan


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
