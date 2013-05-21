###
# Copyright (c) 2013, Valentin Lorentz
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

import supybot.log as log
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('OEIS')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

from .oeis import OEISEntry, ParseError

def query(logger, q):
    return OEISEntry.query(logger=logger,
            fd=utils.web.getUrlFd('http://oeis.org/search?fmt=text&q=%s' % q))

class OEIS(callbacks.Plugin):
    """Add the help for "@plugin help OEIS" here
    This should describe *how* to use this plugin."""
    threaded = True

    def _advsearch(self, irc, msg, args, format_, sequence):
        """<format> <sequence>

        Search with advanced formating options (Python dict-formating)."""
        try:
            (paging, results) = query(self.log, sequence)
        except ParseError:
            irc.error(_('Could not parse OEIS answer.'), Raise=True)
        if results:
            irc.reply(format('%L', map(lambda x:format_ % x, results)))
        else:
            irc.reply(_('No entry matches this sequence.'))
    advsearch = wrap(_advsearch, ['something', 'somethingWithoutSpaces'])

    def _gen(format_, name, doc):
        def f(self, irc, msg, args, sequence):
            self._advsearch(irc, msg, args, format_, sequence)
        f.__doc__ = """<sequence>

        %s""" % doc
        return wrap(f, ['somethingWithoutSpaces'], name=name)

    names = _gen('%(name)s (%(id)s)', 'names',
            'Return names of matching entries.')


Class = OEIS


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
