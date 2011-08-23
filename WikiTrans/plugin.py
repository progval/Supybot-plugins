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

_ = PluginInternationalization('WikiTrans')

import urllib

@internationalizeDocstring
class WikiTrans(callbacks.Plugin):
    """Add the help for "@plugin help WikiTrans" here
    This should describe *how* to use this plugin."""
    threaded = True
    def translate(self, irc, msg, args, src, target, word):
        """<from language> <to language> <word>

        Translates the <word> (also works with expressions) using Wikipedia
        interlanguage links."""
        page = utils.web.getUrlFd('http://%s.wikipedia.org/wiki/%s' %
                (src, urllib.quote_plus(word.replace(' ', '_'))))
        start = ('\t\t\t\t\t<li class="interwiki-%s"><a '
                'href="http://%s.wikipedia.org/wiki/') % \
                (target, target)
        for line in page:
            if line.startswith(start):
                irc.reply(line[len(start):].split('"')[2])
                return
        irc.error(_('No translation found'))
    translate = wrap(translate, ['something', 'something', 'text'])



Class = WikiTrans


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
