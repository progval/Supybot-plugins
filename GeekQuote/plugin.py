###
# Copyright (c) 2004-2005, Kevin Murphy
# Copyright (c) 2008-2009, Benoit Boissinot
# Copyright (c) 2010, Valentin Lorentz
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
import time
import random as modrandom
from xml.dom.minidom import parseString

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class GeekQuote(callbacks.PluginRegexp):
    threaded = True
    callBefore = ['Web']
    regexps = ['geekSnarfer']

    def __init__(self, irc):
        self.__parent = super(GeekQuote, self)
        self.__parent.__init__(irc)
        self.maxqdbPages = 403
        self.lastqdbRandomTime = 0
        self.randomData = {'qdb.us':[],
                           'bash.org':[],
                           'viedemerde.fr':[],
                           'fmylife.com':[],
                           'mylifeisaverage.com':[],
                           'textsfromlastnight.com':[],
                            }

    def callCommand(self, method, irc, msg, *L, **kwargs):
        try:
            self.__parent.callCommand(method, irc, msg, *L, **kwargs)
        except utils.web.Error, e:
            irc.error(str(e))

    _joiner = ' // '
    _tflnReString = r'<textarea readonly="readonly">(?P<text>.*?) http://tfl.nu/[^<]*?</textarea>.*?'\
                    r'<a class="good-night" id="P-(?P<id>\d+)".*?>Good night <span>\((?P<up>\d+)\)</span>.*?'\
                    r'<a class="bad-night" id="N-\d+".*?>Bad night <span>\((?P<down>\d+)\)</span>'
    _mliaReString = r'<div id="s_(?P<id>\d+)" class="story s">\s*'\
                    r'<div class="sc">(?P<text>.*?)</div>.*?'\
                    r'<span class="v_pos">(?P<up>\d+)</span>.*?'\
                    r'<span class="v_neg">(?P<down>\d+)</span>'
    _qdbReString =  r'<span class=qt id=qt\d+>(?P<text>.*?)</span>'
    _gkREDict = {'bash.org': re.compile(r'<p class="qt">(?P<text>.*?)</p>',
                    re.M | re.DOTALL),
                'qdb.us': re.compile(_qdbReString, re.M | re.DOTALL),
                'mylifeisaverage.com':
                    re.compile(_mliaReString, re.M | re.DOTALL),
                'textsfromlastnight.com':
                    re.compile(_tflnReString, re.M | re.DOTALL),}
    _betacieUrl = ('http://api.betacie.com/view/'
                   '%(id)s/nocomment?key=readonly&language=%(lang)s')

    def _gkBackend(self, irc, msg, site, id):
        if not id:
            id = 'random'
        quote = ''
        if id == 'random':
            timeRemaining = int(time.time()) - self.lastqdbRandomTime
            if self.randomData[site]:
                quote = self.randomData[site].pop()
            else:
                if (site == 'qdb.us' and
                            int(time.time()) - self.lastqdbRandomTime <= 90):
                    id = 'browse=%s' % \
                         utils.iter.choice(xrange(self.maxqdbPages))
                quote = self._gkFetchData(site, id, random=True)
        else:
            quote = self._gkFetchData(site, id)
        irc.replies(quote.split(self._joiner), joiner=self._joiner)

    def _gkFetchData(self, site, id, random=False):
        if site in ('viedemerde.fr', 'fmylife.com'):
            if site == 'viedemerde.fr':
                lang = 'fr'
            else:
                lang = 'en'
            url = self._betacieUrl % {'id': id, 'lang': lang}
        elif site == 'textsfromlastnight.com':
            if random:
                page = 'Random-Texts-From-Last-Night.html'
            else:
                page = 'Text-Replies-%s.html' % id
            url = 'http://textsfromlastnight.com/%s' % page
        elif site == 'mylifeisaverage.com':
            if random:
                url = 'http://%s/' % site
                try:
                    html = utils.web.getUrl(url)
                except utils.web.Error, e:
                    self.log.info('%u server returned the error: %s',
                                  site, utils.web.strError(e))
                last = re.search(r'<li class="last"><a href="(\d+)">', html)
                last = int(last.group(1))
                url = 'http://%s/%s' % (site, modrandom.randint(1, last))
            else:
                url = 'http://%s/story/%s' % (site, id)
        else:
            url = 'http://%s/?%s' % (site, id)
        html = ''
        try:
            html = utils.web.getUrl(url)
        except utils.web.Error, e:
            self.log.info('%u server returned the error: %s',
                          site, utils.web.strError(e))
        s = None
        if site in ('viedemerde.fr', 'fmylife.com'):
            def getvalue(dom, tag, default=None):
                v = dom.getElementsByTagName(tag)[0].firstChild
                if v is None and default:
                    return default
                return v.nodeValue.encode("utf-8")

            dom = parseString(html).getElementsByTagName("item")
            if dom:
                try:
                    dom = dom[0]
                    # remove newlines
                    t = self._joiner.join(getvalue(dom, 'text').splitlines())
                    up = getvalue(dom, 'agree', '0')
                    down = getvalue(dom, 'deserved', '0')
                    id = dom.getAttribute('id').encode("utf-8")
                except:
                    self.log.info('server returned the string: %s',
                                  repr(html))
                    raise
                s = "%s #%s (+%s,-%s)" % (t, id, up, down)
                if random and s not in self.randomData[site]:
                    self.randomData[site].append(s)
        elif site in ('mylifeisaverage.com', 'textsfromlastnight.com'):
            for item in self._gkREDict[site].finditer(html):
                d = item.groupdict()
                t = d['text']
                t = utils.web.htmlToText(t, tagReplace='').strip()
                t = self._joiner.join(t.splitlines())
                up = d['up']
                down = d['down']
                id = d['id']
                s = "%s #%s (+%s,-%s)" % (t, id, up, down)
                if random and s:
                    if s not in self.randomData[site]:
                        self.randomData[site].append(s)
                else:
                    break
        else:
            for item in self._gkREDict[site].finditer(html):
                s = item.groupdict()['text']
                s = self._joiner.join(s.splitlines())
                s = utils.web.htmlToText(s)
                if random and s:
                    if s not in self.randomData[site]:
                        self.randomData[site].append(s)
                else:
                    break
        if not s:
	    #self.log.info('server returned the string: %s', repr(html))
            return format('Could not find a quote for id %i.', id)
        else:
            if random:
                # To make sure and remove the first quote from the list so it
                self.randomData[site].pop()
            return s

    def geekSnarfer(self, irc, msg, match):
        r'http://(?:www\.)?(?P<site>bash\.org|qdb\.us|viedemerde\.fr|fmylife\.com|textsfromlastnight\.com)/([?]|story/)?(?P<id>\d+)'
        if not self.registryValue('geekSnarfer', msg.args[0]):
            return
        id = match.groupdict()['id']
        site = match.groupdict()['site']
        self.log.info('Snarfing geekquote %i from %s.', id, site)
        self._gkBackend(irc, msg, site, id)
    geekSnarfer = urlSnarfer(geekSnarfer)

    def geekquote(self, irc, msg, args, id):
        """[<id>]

        Returns a random geek quote from bash.org; the optional argument
        <id> specifies which quote to retrieve.
        """
        site = 'bash.org'
        self._gkBackend(irc, msg, site, id)
    geekquote = wrap(geekquote, [additional(('id', 'geekquote'))])

    def qdb(self, irc, msg, args, id):
        """[<id>]

        Returns a random geek quote from qdb.us; the optional argument
        <id> specifies which quote to retrieve.
        """
        site = 'qdb.us'
        self._gkBackend(irc, msg, site, id)
    qdb = wrap(qdb, [additional(('id', 'qdb'))])

    def vdm(self, irc, msg, args, id):
        """[<id>]

        Returns a random geek quote from viedemerde.fr; the optional argument
        <id> specifies which quote to retrieve.
        """
        site = 'viedemerde.fr'
        self._gkBackend(irc, msg, site, id)
    vdm = wrap(vdm, [additional(('id', 'vdm'))])

    def fml(self, irc, msg, args, id):
        """[<id>]

        Returns a random geek quote from fmylife.com; the optional argument
        <id> specifies which quote to retrieve.
        """
        site = 'fmylife.com'
        self._gkBackend(irc, msg, site, id)
    fml = wrap(fml, [additional(('id', 'fml'))])

    def tfln(self, irc, msg, args, id):
        """[<id>]

        Returns a random quote from textsfromlastnight.com; the optional
        argument <id> specifies which quote to retrieve.
        """
        site = 'textsfromlastnight.com'
        self._gkBackend(irc, msg, site, id)
    tfln = wrap(tfln, [additional(('id', 'tfln'))])

    def mlia(self, irc, msg, args, id):
        """[<id>]

        Returns a random quote from mylifeisaverage.com; the optional
        argument <id> specifies which quote to retrieve.
        """
        site = 'mylifeisaverage.com'
        self._gkBackend(irc, msg, site, id)
    mlia = wrap(mlia, [additional(('id', 'tfln'))])

Class = GeekQuote


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
