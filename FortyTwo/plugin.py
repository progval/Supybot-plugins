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

import re
import time
import fnmatch
from xml.dom import minidom
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('FortyTwo')

class Domain:
    def __init__(self, dom, warnings):
        self.domain = None
        self.purpose = None
        self.resolve = None
        self.http = None
        for node in dom.childNodes:
            if not node.nodeName in 'domain purpose resolve http www'.split():
                warnings.append(_("Unknown node '%s'") % node.nodeName)
                continue
            if node.nodeName == 'www':
                continue
            try:
                data = node.firstChild.data
            except AttributeError:
                # Empty purpose, for instance
                data = ''
            if node.nodeName == 'resolve':
                data = {'No': False, 'Yes': True}[data]
            elif node.nodeName == 'http':
                try:
                    data = int(data)
                except ValueError:
                    data = 0
            self.__dict__.update({node.nodeName: data})
        assert None not in (self.domain, self.purpose, self.resolve, self.http)


@internationalizeDocstring
class FortyTwo(callbacks.Plugin):
    """Add the help for "@plugin help 42Chan" here
    This should describe *how* to use this plugin."""
    @internationalizeDocstring
    def find(self, irc, msg, args, optlist):
        """[--domain <glob>] [--purpose <glob>] [--resolve <true|false>] [--http <integer>]

        Returns all the domains that matches the search. --domain and
        --purpose take a glob (a string with wildcards) that have to match
        the results, --resolves means the domain is resolved, and --http is
        the HTTP response status (000 for a domain that isn't resolved)."""
        def translate(glob):
            return re.compile(fnmatch.translate(glob), re.I)
        domain, purpose = translate('*'), translate('*')
        resolve, http = None, None
        for name, value in optlist:
            if name == 'domain':    domain = translate(value)
            if name == 'purpose':   purpose = translate(value)
            if name == 'resolve':   resolve = value
            if name == 'http':      http = value
        if not hasattr(self, '_lastRefresh') or \
                self._lastRefresh<time.time()-self.registryValue('lifetime'):
            self._refreshCache()
        results = []
        for obj in self._domains:
            if not domain.match(obj.domain) or not purpose.match(obj.purpose):
                continue
            if resolve is not None and obj.resolve != resolve:
                continue
            if http is not None and obj.http != http:
                continue
            results.append(obj.domain)
        if results == []:
            irc.error(_('No such domain'))
        else:
            irc.reply(_(', ').join(results))
    find = wrap(find, [getopts({'domain': 'glob',
                                'purpose': 'glob',
                                'resolve': 'boolean',
                                'http': 'int'})])

    @internationalizeDocstring
    def fetch(self, irc, msg, args):
        """takes no arguments

        Fetches data from the domains list source."""
        self._refreshCache()
        irc.replySuccess()

    @internationalizeDocstring
    def purpose(self, irc, msg, args, domain):
        """<domain>

        Returns the purpose of the given domain."""
        if not hasattr(self, '_lastRefresh') or \
                self._lastRefresh<time.time()-self.registryValue('lifetime'):
            self._refreshCache()
        for obj in self._domains:
            if obj.domain == domain:
                irc.reply(obj.purpose)
                return
        irc.error(_('No such domain'))
    purpose = wrap(purpose, ['somethingWithoutSpaces'])

    def _refreshCache(self):
        self._lastRefresh = time.time()
        xml = utils.web.getUrl(self.registryValue('source'))
        dom = minidom.parseString(xml)
        warnings = []
        root = None
        for child in dom.childNodes:
            if child.nodeName == 'domains':
                root = child
                break
        assert root is not None
        self._domains = [Domain(child, warnings) for child in root.childNodes
                if child.nodeName == 'item']


Class = FortyTwo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
