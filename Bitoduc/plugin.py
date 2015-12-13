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
import json
import itertools
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

SOURCE = 'http://bitoduc.fr/traductions.json'

class Bitoduc(callbacks.Plugin):
    """Interface à bitoduc.fr"""
    def __init__(self, irc):
        self._lock = threading.Lock()
        super(Bitoduc, self).__init__(irc)

    def fetch_dict(self):
        if self._lock.acquire(blocking=False):
            try:
                data = json.loads(utils.web.getUrl(SOURCE).decode())
                self._dict = utils.InsensitivePreservingDict()
                for d in itertools.chain(data['vrais mots'], data['faux mots']):
                    self._dict[d['anglais'].split(' (')[0]] = d['français']
                self._re = re.compile(r'(\b%ss?\b)' % (
                    r's?\b|\b'.join(map(re.escape, self._dict))))
            finally:
                self._lock.release()
            return True
        else:
            return False

    @thread
    @wrap(['text'])
    def bitoduc(self, irc, msg, args, word):
        """<mot anglais>

        Renvoie la traduction française d’un mot."""
        if not hasattr(self, '_dict'):
            r = self.fetch_dict()
            if not r:
                # _dict not yet available
                return
        if word in self._dict:
            irc.reply(self._dict[word])
        else:
            irc.error('Pas de traduction')

    def doPrivmsg(self, irc, msg):
        if callbacks.addressed(irc.nick, msg): #message is not direct command
            return
        channel = msg.args[0]
        if not self.registryValue('correct.enable', channel):
            return
        if not hasattr(self, '_re'):
            threading.Thread(target=self.fetch_dict).start()
            return
        occurences = self._re.findall(msg.args[1])
        if not occurences:
            return
        unique_occurences = []
        occurences_set = set()
        for occurence in occurences:
            if not occurence in self._dict and \
                    occurence.endswith('s') and occurence[0:-1] in self._dict:
                occurence = occurence[0:-1]
            if occurence not in occurences_set:
                unique_occurences.append(occurence)
                occurences_set.add(occurence)
        irc.reply(format('Utilise %L plutôt que %L.',
            ['« %s »' % self._dict[x] for x in unique_occurences],
            ['« %s »' % x for x in unique_occurences])
            .replace(' and ', ' et ')) # fix i18n


Class = Bitoduc


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
