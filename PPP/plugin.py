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
import operator
import requests
import itertools
import functools
import unicode_tex
from ppp_datamodel.communication import Response, Request
from ppp_datamodel import Resource, Sentence, Triple, Missing, List

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

def format_triple(triple, bold):
    if isinstance(triple, Missing):
        if bold:
            return ircutils.bold('?')
        else:
            return '?'
    elif isinstance(triple, Resource):
        return triple.value
    elif isinstance(triple, Triple):
        subtrees = triple.subject, triple.predicate, triple.object
        subtrees = tuple(format_triple(x, bold) for x in subtrees)
        return '(%s, %s, %s)' % subtrees
    elif isinstance(triple, List):
        return '[%s]' % (', '.join(format_triple(x, bold)
                                   for x in triple.list))
    else:
        raise ValueError('%r' % triple)

def handle_badapi(f):
    def newf(self, irc, *args, **kwargs):
        try:
            f(self, irc, *args, **kwargs)
        except requests.exceptions.ConnectionError:
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

class PPP(callbacks.Plugin):
    """A simple plugin to query the API of the Projet Pensées Profondes."""
    threaded = True

    def request(self, channel, request):
        responses = requests.post(self.registryValue('api', channel),
                data=request.as_json()).json()
        return map(Response.from_dict, responses)

    def format_response(self, channel, format_, tree):
        keys = tree._attributes
        if isinstance(tree, Resource):
            if keys.get('value_type', None) == 'math-latex':
                pred = lambda x:unicode_tex.tex_to_unicode_map.get(x, x)
                v = ' '.join(map(pred, keys['value'].split(' ')))
                keys['value'] = v
            try:
                graph = tree.graph
                keys['headline'] = graph['@reverse']['about']['headline'] \
                        .split('\n', 1)[0]
            except (AttributeError, KeyError, IndexError):
                keys['headline'] = _('no headline')
            return [string.Template(format_).safe_substitute(keys)]
        elif isinstance(tree, List):
            pred = functools.partial(self.format_response, channel, format_)
            return filter(bool,
                    itertools.chain.from_iterable(map(pred, tree.list)))
        else:
            return []


    @wrap([optional('channel'), 'text'])
    @handle_badapi
    def query(self, irc, msg, args, channel, sentence):
        """<request>

        Sends a request to the PPP and returns answers."""
        r = Request(id='supybot-%s' % uuid.uuid4().hex,
                language=self.registryValue('language', channel),
                tree=Sentence(value=sentence))
        format_ = self.registryValue('formats.query', channel)
        responses = (x.tree for x in self.request(channel, r))
        formatter = functools.partial(self.format_response, channel, format_)
        L = list(unique(filter(bool,
            itertools.chain.from_iterable(map(formatter, responses)))))
        if L:
            irc.replies(L)
        else:
            irc.error(_('No response'))

    @wrap([optional('channel'), 'text'])
    @handle_badapi
    def triples(self, irc, msg, args, channel, sentence):
        """<request>

        Sends a request to the PPP and returns the triples."""
        r = Request(id='supybot-%s' % uuid.uuid4().hex,
                language=self.registryValue('language', channel),
                tree=Sentence(value=sentence))
        responses = self.request(channel, r)
        responses = map(operator.attrgetter('tree'), responses)
        responses = filter(lambda x:isinstance(x, Triple), responses)
        bold = self.registryValue('formats.bold')
        L = [format_triple(x, bold) for x in responses]
        if L:
            irc.replies(L)
        else:
            irc.error(_('No response'))



Class = PPP


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
