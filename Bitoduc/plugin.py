# -*- coding: utf8 -*-
###
# Copyright (c) 2015, Valentin Lorentz
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
import threading

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Bitoduc')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

SOURCE = 'https://raw.githubusercontent.com/p0nce/bitoduc.fr/master/www.bitoduc.fr/creuille.js'
PATTERN = re.compile(r" *{anglais: '(?P<en>[^(]*)( \(.*\))?' *, francais: '(?P<fr>.*)'}.*")

class Bitoduc(callbacks.Plugin):
    """Interface à bitoduc.fr"""
    def __init__(self, irc):
        self._lock = threading.Lock()
        super(Bitoduc, self).__init__(irc)

    def fetch_dict(self):
        with self._lock:
            self._dict = ircutils.IrcDict()
            fd = utils.web.getUrlFd(SOURCE)
            for line in fd:
                matched = PATTERN.match(line.decode('utf8'))
                if matched:
                    self._dict[matched.group('en')] = matched.group('fr')

    @thread
    @wrap(['text'])
    def bitoduc(self, irc, msg, args, word):
        """<mot anglais>

        Renvoie la traduction française d’un mot."""
        if not hasattr(self, '_dict'):
            self.fetch_dict()
        if word in self._dict:
            irc.reply(self._dict[word])
        else:
            irc.error('Pas de traduction')


Class = Bitoduc


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
