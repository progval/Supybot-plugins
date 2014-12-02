# -*- coding: utf8 -*-
###
# Copyright (c) 2014, Valentin Lorentz
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

import uuid
import string
import requests
import functools
from ppp_datamodel.communication import Response, Request
from ppp_datamodel import Resource, Sentence

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PPP')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class PPP(callbacks.Plugin):
    """A simple plugin to query the API of the Projet Pensées Profondes."""
    threaded = True

    def request(self, channel, request):
        responses = requests.post(self.registryValue('api', channel),
                data=request.as_json()).json()
        return map(Response.from_dict, responses)

    def format_response(self, channel, format_, response):
        keys = response.tree._attributes
        return string.Template(format_).safe_substitute(keys)


    @wrap([optional('channel'), 'text'])
    def query(self, irc, msg, args, channel, sentence):
        """<request>

        Sends a request to the PPP and returns answers."""
        r = Request(id='supybot-%s' % uuid.uuid4().hex,
                language=self.registryValue('language', channel),
                tree=Sentence(value=sentence))
        format_ = self.registryValue('formats.query', channel)
        predicate = functools.partial(self.format_response, channel, format_)
        responses = self.request(channel, r)
        responses = filter(lambda x:isinstance(x.tree, Resource), responses)
        irc.replies(map(predicate, responses))



Class = PPP


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
