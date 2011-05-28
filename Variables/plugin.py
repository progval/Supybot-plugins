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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Variables')

@internationalizeDocstring
class Variables(callbacks.Plugin):
    """Add the help for "@plugin help Variables" here
    This should describe *how* to use this plugin."""

    globalDomains = {}
    channelDomains = {}
    networkDomains = {}

    def _getDomain(self, irc, msg, opts):
        opts = dict(opts)
        if 'domain' not in opts:
            domainType = 'global'
        else:
            domainType = opts['domain']
        if 'name' not in opts:
            if domainType == 'global':
                domainName = 'default'
            elif domainType == 'channel':
                domainName = msg.args[0]
            elif domainType == 'network':
                domainName = irc.network
        else:
            domainName = opts['name']
        domains = {'global': self.globalDomains,
                   'channel': self.channelDomains,
                   'network': self.networkDomains}[domainType]
        if domainName not in domains:
            domains[domainName] = {}
        return domains[domainName]

    @internationalizeDocstring
    def set(self, irc, msg, args, opts, name, value):
        """[--domain <domaintype>] [--name <domainname>] <name> <value>

        Sets a variable called <name> to be <value>, in the domain matching
        the <domaintype> and the <domainname>.
        If <domainname> is not given, it defaults to the current domain
        matching the <domaintype>.
        If <domaintype> is not given, it defaults to the global domain.
        Valid domain types are 'global', 'channel', and 'network'.
        Note that channel domains are channel-specific, but are cross-network.
        """
        domain = self._getDomain(irc, msg, opts)
        domain[name] = value
        irc.replySuccess()
    set = wrap(set, [getopts({'domain': ('literal', ('global', 'network', 'channel')),
                              'name': 'something'}),
                     'something', 'text'])

    @internationalizeDocstring
    def get(self, irc, msg, args, opts, name):
        """[--domain <domaintype>] [--name <domainname>] <name>

        Get the value of the variable called <name>, in the domain matching
        the <domaintype> and the <domainname>.
        If <domainname> is not given, it defaults to the current domain
        matching the <domaintype>.
        If <domaintype> is not given, it defaults to the global domain.
        Valid domain types are 'global', 'channel', and 'network'.
        Note that channel domains are channel-specific, but are cross-network.
        """
        domain = self._getDomain(irc, msg, opts)
        if name in domain:
            irc.reply(domain[name])
        else:
            irc.error('This variable cannot be found.')

    get = wrap(get, [getopts({'domain': ('literal', ('global', 'network', 'channel')),
                              'name': 'something'}),
                     'something'])


Class = Variables


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
