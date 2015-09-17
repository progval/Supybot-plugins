###
# Copyright (c) 2015, Valentin Lorentz
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
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('AlternativeTo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class AlternativeTo(callbacks.PluginRegexp):
    """Access to alternativeto.net"""
    threaded = True
    regexps = ['alternativetoSnarfer']

    def alternativetoSnarfer(self, irc, msg, match):
        """http://alternativeto.net/software/[a-zA-Z_-]+/[^ >]*"""
        channel = msg.args[0]
        if not self.registryValue('snarf', channel):
            return
        url = match(0)
        limit = self.registryValue('limit', channel)
        try:
            irc.reply(self.get_alternatives(url, limit))
        except utils.web.Error:
            pass

    def alternatives(self, irc, msg, args, optlist, software):
        """[--platform <platform>] [--license <free|opensource|commercial]] <software>

        Returns a list of alternatives to the <software>."""
        if '/' in software:
            irc.error(_('Software name may not contain a / character.'),
                    Raise=True)
        url = 'http://alternativeto.net/software/%s/?%s' % (software,
                '&'.join('%s=%s' % x for x in optlist))
        channel = msg.args[0]
        limit = self.registryValue('limit', channel)
        try:
            irc.replies(self.get_alternatives(url, limit))
        except utils.web.Error:
            irc.error(_('Software not found.'), Raise=True)
    alternatives = wrap(alternatives, [
        getopts({'platform': 'somethingWithoutSpaces',
                 'license': ('literal', ['free', 'opensource', 'commercial'])}),
        'somethingWithoutSpaces'])

    def get_alternatives(self, url, limit):
        page = utils.web.getUrl(url)
        if sys.version_info[0] >= 3 and isinstance(page, bytes):
            page = page.decode()
        useful = page.split(r".setTargeting('Alts', ['", 1)[1] \
                .split(r"']);", 1)[0]
        L = [x.split('---')[0].replace('-', ' ')
                for x in useful.split("','")]
        if limit and len(L) > limit:
            L = L[0:limit] + [_('%d more') % len(L) - limit]
        return L


Class = AlternativeTo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
