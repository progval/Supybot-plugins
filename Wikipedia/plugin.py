###
# Copyright (c) 2010, quantumlemur
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
import string
import urllib
import StringIO
import lxml.html
from lxml import etree
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

# plugins.wikipedia.snippetStyle in ['sentence','paragraph','none']


class Wikipedia(callbacks.Plugin):
    """Add the help for "@plugin help Wikipedia" here
    This should describe *how* to use this plugin."""
    threaded = True


    def wiki(self, irc, msg, args, search):
        """<search term>

        Returns the first paragraph of a Wikipedia article"""
# first, we get the page
        addr = 'http://en.wikipedia.org/wiki/Special:Search?search=%s' % urllib.quote_plus(search)
        try:
            article = utils.web.getUrl(addr)
        except:
            irc.reply('Hmm, something went wrong fetching the page.  I\'m highlighting quantumlemur so he can take a look.')
            return
# parse the page
        tree = lxml.html.document_fromstring(article)
# check if it gives a "Did you mean..." redirect
        didyoumean = tree.xpath('//div[@class="searchdidyoumean"]/a[@title="Special:Search"]')
        if didyoumean:
            redirect = didyoumean[0].text_content().strip()
            irc.reply('I didn\'t find anything for "%s". Did you mean "%s"?' % (search, redirect))
            addr = 'http://en.wikipedia.org%s' % didyoumean[0].get('href')
            article = utils.web.getUrl(addr)
            tree = lxml.html.document_fromstring(article)
            search = redirect
# check if it's a page of search results (rather than an article), and if so, retrieve the first result
        searchresults = tree.xpath('//div[@class="searchresults"]/ul/li/a')
        if searchresults:
            redirect = searchresults[0].text_content().strip()
            irc.reply('I didn\'t find anything for "%s", but here\'s the result for "%s":' % (search, redirect))
            addr = 'http://en.wikipedia.org%s' % searchresults[0].get('href')
            article = utils.web.getUrl(addr)
            tree = lxml.html.document_fromstring(article)
            search = redirect
# otherwise, simply return the title and whether it redirected
        else:
            redirect = re.search('\(Redirected from <a href=[^>]*>([^<]*)</a>\)', article)
            if redirect:
                redirect = tree.xpath('//div[@id="contentSub"]/a')[0].text_content().strip()
                title = tree.xpath('//*[@class="firstHeading"]')
                title = title[0].text_content().strip()
                irc.reply('"%s" (Redirect from "%s"):' % (title, redirect))
# extract the address we got it from
        addr = re.search('Retrieved from "<a href="([^"]*)">', article)
        addr = addr.group(1)
# check if it's a disambiguation page
        disambig = tree.xpath('//table[@id="disambigbox"]')
        if disambig:
            disambig = tree.xpath('//div[@id="bodyContent"]/ul/li/a')
            disambig = disambig[:5]
            disambig = [item.text_content() for item in disambig]
            r = utils.str.commaAndify(disambig)
            irc.reply('%s is a disambiguation page.  Possible results are: %s' % (addr, r))
# or just as bad, a page listing events in that year
        elif re.search('This article is about the year [\d]*\.  For the [a-zA-Z ]* [\d]*, see', article):
            irc.reply('"%s" is a page full of events that happened in that year.  If you were looking for information about the number itself, try searching for "%s_(number)", but don\'t expect anything useful...' % (search, search))
        else:
##### etree!
            p = tree.xpath("//div[@id='bodyContent']/p[1]")[0]
            p = p.text_content()
            p = p.strip()
            p = p.encode('utf-8')
# and finally, return what we've got
            irc.reply(addr)
            irc.reply(p)
    wiki = wrap(wiki, ['text'])




#    def wikiold(self, irc, msg, args, search):
#        """<Wikipedia search term>
#
#        Returns the first paragraph of a Wikipedia article"""
## first, we get the page
#        try:
#            article = utils.web.getUrl('http://en.wikipedia.org/wiki/Special:Search?search=%s' % urllib.quote_plus(search))
#        except:
#            irc.reply('Hmm, looks like we broke Wikipedia.  Try again later?')
#            return
## check if it gives a "Did you mean..." redirect
#        if 'class="searchdidyoumean"' in article:
#            redirect = re.search('class="searchdidyoumean">[^>]*title="Special:Search">(.*?)</div>', article)
#            redirect = redirect.group(1)
#            redirect = utils.web.htmlToText(redirect, tagReplace="")
#            irc.reply('I didn\'t find anything for "%s". Did you mean "%s"?' % (search, redirect))
#            search = redirect
#            article = utils.web.getUrl('http://en.wikipedia.org/wiki/Special:Search?search=%s' % urllib.quote_plus(search))
## then check if it's a page of search results (rather than an article), and if so, retrieve the first result
#        if '<ul class=\'mw-search-results\'>' in article:
#            article = article[article.find('<ul class=\'mw-search-results\'>'):len(article)]
#            article = article[article.find('/'):article.find('" title=')]
#            redirect = article[article.find('/')+1 : ]
#            redirect = redirect[redirect.find('/')+1 : ]
#            redirect = urllib.unquote(redirect)
#            irc.reply('I didn\'t find anything for "%s", but here\'s the result for "%s":' % (search, redirect))
#            article = utils.web.getUrl('http://en.wikipedia.org%s' % article.replace(' ', '+'))
#            search = redirect
## otherwise, simply return the title and whether it redirected
#        else:
#            title = re.search('class="firstHeading">([^<]*)</h1>', article)
#            redirect = re.search('\(Redirected from <a href=[^>]*>([^<]*)</a>\)', article)
#            if redirect:
#                irc.reply('"%s" (Redirect from "%s"):' % (title.group(1), redirect.group(1)))
#                search = title.group(1)
## extract the address we got it from
#        addr = re.search('Retrieved from "<a href="([^"]*)">', article)
#        addr = addr.group(1)
## this is a funny html thingie that shows up when there are multiple boxes on a page, and causes problems
#        article = re.sub('<p><br /></p>', '', article)
## I hope this doesn't take out anything it shouldn't...
#        article = re.sub('<p><i>For other uses of ', '', article)
## check if it's a disambiguation page
#        if re.search('This <a href="[^>]*>disambiguation</a> page lists articles associated with the same title', article):
#            irc.reply('"%s" leads to a disambiguation page, so it would be kind of hard to list the results from it in IRC.  I\'d suggest checking out the page yourself: %s' % (search, addr))
#            return
## or just as bad, a page listing events in that year
#        elif re.search('This article is about the year [\d]*\.  For the [a-zA-Z ]* [\d]*, see', article):
#            irc.reply('"%s" is a page full of events that happened in that year.  If you were looking for information about the number itself, try searching for "%s_(number)", but don\'t expect anything useful...' % (search, search))
#            return
## remove the coordinates if the article includes them
#        coord = article.find('title="Geographic coordinate system">')
#        p = article.find('<p>')
#        if p < coord and coord - p < 150:
#            if self.registryValue('debug'):
#                irc.reply('\x0314coordinates found at %s...' % article.find('title="Geographic coordinate system'))
#            article = article[article.find('title="Geographic coordinate system') : len(article)]
#            article = article[article.find('</p>')+5 : ]
## step through and count up how many nested tables there are before the first proper paragraph...
#        tables = 0
#        while article.find('table') < article.find('<p>') or tables > 0:
#            tag = re.search('</?table', article)
#            if '/' in tag.group(0):
#                tables += -1
#                if self.registryValue('debug'):
#                    irc.reply('\x0314table closed at %s/%s, beheading...' % (tag.start(), len(article)))
#            else:
#                tables += 1
#                if self.registryValue('debug'):
#                    irc.reply('\x0314table opened at %s/%s, beheading...' % (tag.start(), len(article)))
#            article = article[tag.end():]
#        if self.registryValue('debug'):
#            irc.reply('\x0314p at %s, /p at %s' % (article.find('<p>'), article.find('</p>')))
## finally, isolate the first proper paragraph and strip the HTML
#        article = article[article.find('<p>'):article.find('</p>')]
#        article = utils.web.htmlToText(article, tagReplace="")
## remove any citations from the paragraph
#        article = re.sub('\[\d*\]', '', article)
#        article = re.sub('\[citation needed\]', '', article)
## and finally, return what we've got
#        irc.reply(addr)
#        irc.reply(article)
#    wikiold = wrap(wikiold, ['text'])

Class = Wikipedia


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
