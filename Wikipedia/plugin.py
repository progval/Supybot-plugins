###
# Copyright (c) 2010, quantumlemur
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


import re
import sys
import json
import urllib
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Wikipedia')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

if sys.version_info[0] >= 3:
    quote_plus = urllib.parse.quote_plus
    urlencode = urllib.parse.urlencode
else:
    quote_plus = urllib.quote_plus
    urlencode = urllib.urlencode


class Wikipedia(callbacks.Plugin):
    """Add the help for "@plugin help Wikipedia" here
    This should describe *how* to use this plugin."""
    threaded = True

    def queryApi(self, network, channel, params):
        params = params.copy()
        params["format"] = "json"
        addr = 'https://%s/w/api.php?%s' % \
                    (self.registryValue('url', channel=channel, network=network),
                     urlencode(params))
        resp = utils.web.getUrl(addr)
        if sys.version_info[0] >= 3:
            resp = resp.decode()
        return json.loads(resp)

    def getExtract(self, network, channel, title):
        """Returns (redirect_target, extract); either may be None."""
        params = dict(
            action="query",
            prop="extracts",
            exchars=700,  # should fit with a single @more
            titles=title,
            explaintext="true",  # get result in plain text instead of HTML
            exsectionformat="plain",  # don't get wikitext
            redirects="",  # resolve redirects
        )
        resp = self.queryApi(network, channel, params)
        if "-1" in resp["query"]["pages"]:
            return (None, None)
        if "redirects" in resp["query"]:
            redirect = resp["query"]["redirects"][-1]["to"]
        else:
            redirect = None
        pages = resp["query"]["pages"]
        return (redirect, next(iter(pages.values()))["extract"])

    def searchPage(self, network, channel, search, titleOnly):
        if titleOnly:
            search = "intitle:" + search

        params = dict(
            action="query",
            list="search",
            redirects="",  # resolve redirect
            srsearch=search,
        )
        resp = self.queryApi(network, channel, params)
        if "suggestion" in resp["query"]["searchinfo"]:
            return resp["query"]["searchinfo"]["suggestion"]
        if resp["query"]["search"]:
            return resp["query"]["search"][0]["title"]
        return None

    @internationalizeDocstring
    def wiki(self, irc, msg, args, search):
        """<search term>

        Returns the first paragraph of a Wikipedia article"""
        network = irc.network
        channel = msg.channel
        showRedirects = self.registryValue(
                'showRedirects', channel=channel, network=network)
        title = None
        prefixes = ""

        (redirect, extract) = self.getExtract(network, channel, search)

        if redirect and showRedirects:
            prefixes += _('"%s" (Redirected from "%s"): ') % (redirect, search)

        if not extract:
            # No exact (or redirected) match: use the search
            title = self.searchPage(network, channel, search, True)

            if not title:
                # No results on titles only, search harder and always point it
                # out
                title = self.searchPage(network, channel, search, False)
                showRedirects = True

            (redirect, extract) = self.getExtract(network, channel, title)
            redirect = redirect or title

            if not redirect:
                irc.error(_('Not found, or page malformed.*'))

            if showRedirects:
                prefixes += _('I didn\'t find anything for "%s". '
                              'Did you mean "%s"? ') % (search, redirect)

        addr = "https://%s/wiki/%s" % (
            self.registryValue('url', channel=channel, network=network),
            quote_plus(redirect or title or search)
        )

        extract = utils.str.normalizeWhitespace(extract)

        irc.reply(format(_("%s%s - Retrieved from %u"),
                  prefixes, extract, addr))
    wiki = wrap(wiki, ['text'])



Class = Wikipedia


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
