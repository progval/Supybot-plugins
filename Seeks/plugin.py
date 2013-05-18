###
# Copyright (c) 2010, Pablo Joubert
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

import urllib
import json

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

class Seeks(callbacks.Plugin):
    """Simply calls a seeks node, requesting json"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Seeks, self)
        self.__parent.__init__(irc)
        # should be changed for your node

    def search(self, irc, msg, args, query):
        """<query>

        Searches the <query> in a seeks node."""
        query_str = self.registryValue('url', msg.args[0])
        query = urllib.quote(query).replace('%20', '+')
        raw_page = urllib.urlopen(query_str + query)
        page = raw_page.read()
        try:
            content = json.loads(page)
        except:
            raise
            irc.error("Server's JSON is corrupted")
            return
        print repr(content)
        snippets = content["snippets"]
        if len(snippets) == 0:
            irc.reply('No results')
            return
        separator = self.registryValue('separator', msg.args[0])
        format_ = self.registryValue('format', msg.args[0])
        number = self.registryValue('number', msg.args[0])
        answer = " / ".join(format_ % x for x in snippets[:number-1])
        irc.reply(answer)

    search = wrap(search, ['text'])

Class = Seeks

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
