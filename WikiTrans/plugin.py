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

import sys
import json
import operator
import itertools

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('WikiTrans')

import urllib
from xml.dom import minidom

if sys.version_info[0] == 2:
    quote_plus = urllib.quote_plus
else:
    quote_plus = urllib.parse.quote_plus

class WordNotFound(Exception):
    pass
class Untranslatable(Exception):
    pass
class ApiError(Exception):
    pass

MAX_ENTITIES_SEARCH = 50
wikidata_search_url = 'https://www.wikidata.org/w/api.php?format=json&' + \
        'action=wbsearchentities&language=%(language)s&search=%(search)s'
wikidata_query_url = 'https://www.wikidata.org/w/api.php?format=json&' + \
        'action=wbgetentities&ids=%(ids)s&props=aliases|labels&' + \
        'languages=%(languages)s'
def wikidata_translate(src, target, word):
    # Get matching entity IDs
    url = wikidata_search_url % {'language': src, 'search': quote_plus(word)}
    data = json.loads(utils.web.getUrl(url).decode())
    if not data['search']:
        raise WordNotFound()
    entities = map(operator.itemgetter('id'), data['search'])

    # Get labels of those entities
    entities_str = '|'.join(itertools.islice(entities, MAX_ENTITIES_SEARCH))
    url = wikidata_query_url % {'languages': '%s|%s' % (src, target),
                                'ids': entities_str}
    data = json.loads(utils.web.getUrl(url).decode())

    if 'entities' not in data:
        # No 'entity' attribute -> those entities have no labels
        # in the desired langues.
        raise Untranslatable()

    # Remove entities whose label/aliases do not match exactly
    entities = data['entities']
    if sys.version_info[0] < 3:
        word = word.decode('utf8')
    word = word.lower()
    pred = lambda x: (word == x['labels'][src]['value'].lower() or
                      word in (y['value'].lower()
                               for y in x.get('aliases', {}).get(src, [])))
    entities = filter(pred, entities.values())

    # Join all possible translations
    r = format('%L', [x['labels'][target]['value']
                      for x in entities
                      if target in x.get('labels', {})])

    if not r:
        raise Untranslatable()
    else:
        return r



# lllimit means "langlink limits". If we don't give this parameter, output
# will be restricted to the ten first links.
wikipedia_url = 'http://%s.wikipedia.org/w/api.php?action=query&' + \
        'format=xml&prop=langlinks&redirects&lllimit=300&titles=%s'
def wikipedia_translate(src, target, word):
    try:
        node = minidom.parse(utils.web.getUrlFd(wikipedia_url % (src,
                quote_plus(word))))
    except:
        # Usually an urllib error
        raise WordNotFound()

    # The tree containing the langs links
    expectedNodes = 'api query pages page langlinks'.split()
    # Iterate while the node is not a langlink
    while node.nodeName != 'langlinks':
        if not node.hasChildNodes():
            raise WordNotFound()
        node = node.firstChild
        # If this page is a redirection to another:
        if node.nodeName in ('redirects', 'normalized'):
            newword = node.firstChild.getAttribute('to')
            return wikipedia_translate(src, target, newword)
        expectedNode = expectedNodes.pop(0)
        # Iterate while the node is not valid
        while node.nodeName != expectedNode:
            node = node.nextSibling
        if node.nodeName != expectedNode:
            raise ApiError()

    link = node.firstChild
    # Iterate through the links, until we find the one matching the target
    # language
    while link is not None:
        assert link.tagName == 'll'
        if link.getAttribute('lang') != target:
            link = link.nextSibling
            continue
        if sys.version_info[0] < 3:
            return link.firstChild.data.encode('utf-8', 'replace')
        else:
            return link.firstChild.data
    # Too bad :-(
    # No lang links available for the target language
    raise Untranslatable()

def translate(src, target, word):
    try:
        return wikidata_translate(src, target, word)
    except (WordNotFound, Untranslatable) as e:
        return wikipedia_translate(src, target, word)

@internationalizeDocstring
class WikiTrans(callbacks.Plugin):
    """Add the help for "@plugin help WikiTrans" here
    This should describe *how* to use this plugin."""
    threaded = True

    def translate(self, irc, msg, args, src, target, word):
        """<from language> <to language> <word>

        Translates the <word> (also works with expressions) using Wikidata
        labels and Wikipedia interlanguage links."""
        try:
            irc.reply(translate(src, target, word))
        except (WordNotFound, Untranslatable):
            irc.error(_('This word can\'t be found or translated using '
                        'Wikidata and Wikipedia'))
        except ApiError:
            irc.error(_('Something went wrong with Wikipedia/data API.'))
    translate = wrap(translate, ['something', 'something', 'text'])

    def wikidata(self, irc, msg, args, src, target, word):
        """<from language> <to language> <word>

        Translates the <word> (also works with expressions) using Wikipedia
        interlanguage links."""
        try:
            irc.reply(wikidata_translate(src, target, word))
        except WordNotFound:
            irc.error(_('This word can\'t be found on Wikidata'))
        except Untranslatable:
            irc.error(_('No translation found'))
        except ApiError:
            irc.error(_('Something went wrong with Wikidata API.'))
    wikidata = wrap(wikidata, ['something', 'something', 'text'])

    def wikipedia(self, irc, msg, args, src, target, word):
        """<from language> <to language> <word>

        Translates the <word> (also works with expressions) using Wikipedia
        interlanguage links."""
        try:
            irc.reply(wikipedia_translate(src, target, word))
        except WordNotFound:
            irc.error(_('This word can\'t be found on Wikipedia'))
        except Untranslatable:
            irc.error(_('No translation found'))
        except ApiError:
            irc.error(_('Something went wrong with Wikipedia API.'))
    wikipedia = wrap(wikipedia, ['something', 'something', 'text'])



Class = WikiTrans


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
