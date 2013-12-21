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

REGEXP = '[cçk]^([o0öôØ]^[i1ïî]|[i1]^[o0Ø])^[nñ]'
_regexp = re.compile(REGEXP.replace('^', ''), re.I)
def replacer(match):
    coin = match.group(0)
    assert len(coin) == 4
    reverse = coin[1] in 'i1I'
    if reverse:
        assert coin[2] in 'oO0'
        coin = coin[0] + coin[2] + coin[1] + coin[3]
        reverse = True
    strike = 'Ø' in coin
    if strike:
        coin = coin.replace('Ø', 'o')
    pan = ''
    if coin[0] in 'ck':
        pan += 'p'
    elif coin[0] in 'CK':
        pan += 'P'
    elif coin[0] == 'ç':
        pan += '\u0327p'
    elif coin[0] == 'Ç':
        pan += '\u0327P'
    else:
        raise AssertionError(coin)
    if strike:
        pan += '\u0336'
    if coin[1] == '0' or coin[2] == '1':
        pan += '4'
    elif coin[1:3] in 'Oï OÏ oÏ Öi ÖI öI Öï ÖÏ öÏ'.split(' '):
        pan += 'Ä'
    elif coin[1:3] in 'Oî OÎ oÎ Ôi ÔI ôI Ôî ÔÎ ôÎ'.split(' '):
        pan += 'Â'
    elif coin[1:3] in 'öi öï oï'.split(' '):
        pan += 'ä'
    elif coin[1:3] in 'ôi ôî oî'.split(' '):
        pan += 'â'
    elif coin[1] in 'ôÔöÖ' and coin[2] in 'îÎïÏ':
        if coin[0] in 'kK':
            return'KOINKOINKOINPANGPANGPANG'
        elif coin[0] in 'ĉĈ':
            return'ĈOINĈOINĈOINPANPANPAN'
        else:
            return'COINCOINCOINPANPANPAN'
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
    elif coin[3] == 'ñ':
        pan += 'ñ'
    elif coin[3] == 'Ñ':
        pan += 'Ñ'
    else:
        raise AssertionError(coin)
    if coin[0] == 'k':
        pan += 'g'
    elif coin[0] == 'K':
        pan += 'G'
    if reverse:
        pan = pan.replace('a', 'ɐ')
        pan = pan.replace('A', '∀')
        pan = pan.replace('4', 'ㄣ')
    return pan

def snarfer_generator():
    def coinSnarfer(self, irc, msg, match):
        if self.registryValue('enable', msg.args[0]):
            txt = msg.args[1]
            txt = txt.replace('\u200b', '')
            txt = txt.replace('Ο', 'O')
            txt = txt.replace('>o_/', '>x_/').replace('\_o<', '\_x<')
            txt = txt.replace('>O_/', '>x_/').replace('\_O<', '\_x<')
            irc.reply(_regexp.sub(replacer, txt), prefixNick=False)
    regexp = '(?i).*(%s|>^o^_^/|\^_^[Oo]^<).*' % REGEXP
    regexp = regexp.replace('^', '\u200b*')
    coinSnarfer.__doc__ = regexp
    return coinSnarfer

class Coinpan(callbacks.PluginRegexp):
    """Add the help for "@plugin help Coinpan" here
    This should describe *how* to use this plugin."""

    regexps = ['coinSnarfer']
    coinSnarfer = snarfer_generator()


Class = Coinpan


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
