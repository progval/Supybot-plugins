###
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
import json

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('ERepublik')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

def getCitizen(irc, name):
    try:
        if name.isdigit():
            base = 'http://api.erpk.org/citizen/profile/%s.json?key=nIKh0F7U'
            return json.load(utils.web.getUrlFd(base % name))
        else:
            base = 'http://api.erpk.org/citizen/search/%s/1.json?key=nIKh0F7U'
            data = json.load(utils.web.getUrlFd(base % name))
            return getCitizen(irc, data[0]['id'])
    except:
        irc.error(_('This citizen does not exist.'), Raise=True)

def flatten_subdicts(dicts):
    """Change dict of dicts into a dict of strings/integers. Useful for
    using in string formatting."""
    flat = {}
    for key, value in dicts.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                if isinstance(subvalue, dict):
                    for subsubkey, subsubvalue in subvalue.items():
                        flat['%s__%s__%s' % (key, subkey, subsubkey)] = subsubvalue
                else:
                    flat['%s__%s' % (key, subkey)] = subvalue
        else:
            flat[key] = value
    return flat

class ERepublik(callbacks.Plugin):
    threaded = True

    def _advinfo(self, irc, msg, args, format_, name):
        """<format> <name|id>

        Returns informations about a citizen with advanced formating."""
        citizen = flatten_subdicts(getCitizen(irc, name))
        try:
            irc.replies(map(lambda x:x%citizen, format_.split('\\n')))
        except KeyError:
            raise
            irc.error(_('Invalid format.'), Raise=True)
    advinfo = wrap(_advinfo, ['something', 'text'])

    def _gen(format_, name, doc):
        format_ = re.sub('[ \n]+', ' ', format_)
        def f(self, irc, msg, args, sequence):
            self._advinfo(irc, msg, args, format_, sequence)
        f.__doc__ = """<name|id>

        %s""" % doc
        return wrap(f, ['text'], name=name)

    info = _gen("""Name: %(name)s (ID: %(id)s), Level: %(level)s, Strength:
    %(strength)s, Residence: %(residence__country__name)s, Citizenship:
    %(citizenship__name)s, Rank: %(rank__name)s, Party: %(party__name)s, MU:
    %(army__name)s.
    """,
    'info',
    'Returns general informations about a citizen.')

    @internationalizeDocstring
    def medals(self, irc, msg, args, name):
        """<name|id>

        Displays the citizen's medals."""
        citizen = getCitizen(irc, name)
        medals = ['%s (%i)' % x for x in citizen['medals'].items() if x[1]]
        irc.reply(_('%s has the following medal(s): %s') %
                  (name, ', '.join(medals)))
    medals = wrap(medals, ['text'])


ERepublik = internationalizeDocstring(ERepublik)
Class = ERepublik


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
