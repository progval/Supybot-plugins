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
import json
import string
import operator
import requests
import itertools
import functools
import urllib.parse
import urllib.error

import unicode_tex
from pyld import jsonld

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

def handle_badapi(f):
    def newf(self, irc, *args, **kwargs):
        try:
            f(self, irc, *args, **kwargs)
        except utils.web.Error:
            irc.error('Could not connect to the API.')
    newf.__name__ = f.__name__
    newf.__doc__ = f.__doc__
    return newf

def unique(L):
    seen = set()
    for item in L:
        if item not in seen:
            seen.add( item )
            yield item

def best_locale(available, expected):
    if expected in available:
        # language + country match
        return expected
    languages = {a.split('-')[0] for a in available}
    languages = {l for l in languages if l == expected}
    if languages:
        # language match
        return list(languages)[0]

    # no match
    return list(available)[0]

def format_result(result, expected_locale, bold):
    names = {d['@language']: d['@value']
             for d in result.get('http://schema.org/name', [])}
    alt_names = {d['@language']: d['@value']
             for d in result.get('http://schema.org/alternateName', [])}

    if names or alt_names:
        name_locale = best_locale(set(names) | set(alt_names), expected_locale)
        name = names.get(name_locale, alt_names.get(name_locale))
    else:
        name = None

    descriptions = {d['@language']: d['@value']
             for d in result.get('http://schema.org/description', [])}
    if descriptions:
        desc_locale = best_locale(set(descriptions), expected_locale)
        description = descriptions[desc_locale]
    else:
        description = None

    if bold:
        name = ircutils.bold(name)

    if name and description:
        return '%s (%s)' % (name, description)
    elif name:
        return name
    elif description:
        return description
    else:
        return None


class PPP(callbacks.Plugin):
    """A simple plugin to query the API of the Projet Pensées Profondes."""
    threaded = True

    def request(self, channel, request, language):
        params = urllib.parse.urlencode({'q': request, 'lang': language})
        url = self.registryValue('api', channel) + '?' + params

        content = utils.web.getUrlContent(url, size=10**7, headers={
            'Accept-Language': language})
        return json.loads(content.decode())

    _opts = {'locale': 'somethingWithoutSpaces',
            'lang': 'somethingWithoutSpaces',
            'language': 'somethingWithoutSpaces',
            }
    @wrap([optional('channel'), getopts(_opts), 'text'])
    @handle_badapi
    def query(self, irc, msg, args, channel, optlist, request):
        """[--locale <language>] <request>

        Sends a request to the PPP and returns answers."""
        locale = self.registryValue('language', channel)
        bold = self.registryValue('formats.bold', channel)

        for (key, value) in optlist:
            if key in ('locale', 'lang', 'language'):
                locale = value

        response = self.request(channel, request, locale)
        response = jsonld.expand(response)
        seen = set()
        replies = []
        def add_reply(r):
            normalized = r.strip()
            if normalized in seen:
                return
            replies.append(r)
            seen.add(normalized)
        for collection in response:
            for member in collection['http://www.w3.org/ns/hydra/core#member']:
                for result in member['http://schema.org/result']:
                    add_reply(format_result(result, locale, bold))


        irc.replies(replies)



Class = PPP


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
