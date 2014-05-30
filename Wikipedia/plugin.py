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
import string
import urllib
import lxml.html
from lxml import etree
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
if sys.version_info[0] < 3:
    import StringIO
else:
    from io import StringIO
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
else:
    quote_plus = urllib.quote_plus


class Wikipedia(callbacks.Plugin):
    """Add the help for "@plugin help Wikipedia" here
    This should describe *how* to use this plugin."""
    threaded = True


    @internationalizeDocstring
    def wiki(self, irc, msg, args, search):
        """<search term>

        Returns the first paragraph of a Wikipedia article"""
        reply = ''
        # first, we get the page
        addr = 'https://%s/wiki/Special:Search?search=%s' % \
                    (self.registryValue('url', msg.args[0]),
                     quote_plus(search))
        article = utils.web.getUrl(addr)
        if sys.version_info[0] >= 3:
            article = article.decode()
        # parse the page
        tree = lxml.html.document_fromstring(article)
        # check if it gives a "Did you mean..." redirect
        didyoumean = tree.xpath('//div[@class="searchdidyoumean"]/a'
                                '[@title="Special:Search"]')
        if didyoumean:
            redirect = didyoumean[0].text_content().strip()
            if sys.version_info[0] < 3:
                if isinstance(redirect, unicode):
                    redirect = redirect.encode('utf-8','replace')
                if isinstance(search, unicode):
                    search = search.encode('utf-8','replace')
            reply += _('I didn\'t find anything for "%s".'
                       'Did you mean "%s"? ') % (search, redirect)
            addr = self.registryValue('url', msg.args[0]) + \
                   didyoumean[0].get('href')
            if not article.startswith('http'):
                article = utils.web.getUrl('https://' + addr)
            if sys.version_info[0] >= 3:
                article = article.decode()
            tree = lxml.html.document_fromstring(article)
            search = redirect
        # check if it's a page of search results (rather than an article), and
        # if so, retrieve the first result
        searchresults = tree.xpath('//div[@class="searchresults"]/ul/li/a')
        if searchresults:
            redirect = searchresults[0].text_content().strip()
            reply += _('I didn\'t find anything for "%s", but here\'s the '
                     'result for "%s": ') % (search, redirect)
            addr = self.registryValue('url', msg.args[0]) + \
                   searchresults[0].get('href')
            article = utils.web.getUrl(addr)
            if sys.version_info[0] >= 3:
                article = article.decode()

            tree = lxml.html.document_fromstring(article)
            search = redirect
        # otherwise, simply return the title and whether it redirected
        else:
            redirect = re.search('\(%s <a href=[^>]*>([^<]*)</a>\)' %
                                 _('Redirected from'), article)
            if redirect:
                redirect = tree.xpath('//div[@id="contentSub"]/a')[0]
                redirect = redirect.text_content().strip()
                title = tree.xpath('//*[@class="firstHeading"]')
                title = title[0].text_content().strip()
                if sys.version_info[0] < 3:
                    if isinstance(title, unicode):
                        title = title.encode('utf-8','replace')
                    if isinstance(redirect, unicode):
                        redirect = redirect.encode('utf-8','replace')
                reply += '"%s" (Redirect from "%s"): ' % (title, redirect)
        # extract the address we got it from
        addr = re.search(_('Retrieved from') + ' "<a dir="ltr" href="([^"]*)">', article)
        addr = addr.group(1)
        # check if it's a disambiguation page
        disambig = tree.xpath('//table[@id="disambigbox"]')
        if disambig:
            disambig = tree.xpath('//div[@id="bodyContent"]/ul/li/a')
            disambig = disambig[:5]
            disambig = [item.text_content() for item in disambig]
            r = utils.str.commaAndify(disambig)
            reply += _('%s is a disambiguation page. '
                       'Possible results are: %s') % (addr, r)
        # or just as bad, a page listing events in that year
        elif re.search(_('This article is about the year [\d]*\. '
                       'For the [a-zA-Z ]* [\d]*, see'), article):
            reply += _('"%s" is a page full of events that happened in that '
                      'year.  If you were looking for information about the '
                      'number itself, try searching for "%s_(number)", but '
                      'don\'t expect anything useful...') % (search, search)
        else:
            ##### etree!
            p = tree.xpath("//div[@id='mw-content-text']/p[1]")
            if len(p) == 0 or addr.endswith('Special:Search'):
                reply += _('Not found, or page bad formed.')
            else:
                p = p[0]
                p = p.text_content()
                p = p.strip()
                if sys.version_info[0] < 3:
                    if isinstance(p, unicode):
                        p = p.encode('utf-8', 'replace')
                    if isinstance(reply, unicode):
                        reply = reply.encode('utf-8','replace')
                reply += '%s %s' % (p, ircutils.bold(addr))
        reply = reply.replace('&amp;','&')
        irc.reply(reply)
    wiki = wrap(wiki, ['text'])



Class = Wikipedia


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
