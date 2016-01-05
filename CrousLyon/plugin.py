# -*- coding: utf8 -*-
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

import datetime
import requests
try:
    from defusedxml import ElementTree
except ImportError:
    from xml.etree import ElementTree

import supybot.utils as utils
import supybot.plugins as plugins
from supybot.commands import first, wrap
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('CrousLyon')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

NAMES = {
        'monod': 351,
        'descartes': 230,
        'jussieu': 240,
        }
INTERESTING = {
        351: # Monod
            ('Plats',),
        230: # Descartes
            ('PLATS',),
        }
URL = 'http://irestos.nuonet.fr/generation.php?crous=21&resto=%d&ext=xml'
BLACKLIST = ['variées', 'variés', 'du chef', 'buffet']
def get(id_):
    text = requests.get(URL % id_, stream=True).raw.read()
    text = text.decode(utils.web.getEncoding(text) or 'utf8')
    root = ElementTree.fromstring(text)
    assert root.tag == 'root', root
    resto = root[0]
    assert resto.tag == 'resto', resto
    res = []
    for menu in resto:
        assert menu.tag == 'menu', menu
        date = menu.attrib['date']
        parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        day_limit = datetime.datetime.now() - datetime.timedelta(hours=14)
        if parsed_date < day_limit:
            continue
        midi = menu[0]
        assert midi.tag == 'midi', midi
        interesting = INTERESTING.get(id_, None)
        if interesting:
            meals = [x.text for x in midi
                     if x.attrib['nom'].startswith(interesting)]
        else:
            meals = [x.text for x in midi
                     if not any(y in x.text.lower() for y in BLACKLIST)]
        meals = [x.strip().replace('\n', ' ; ').strip() for x in meals
                 if x.strip()]
        res.append((date, meals))
    return res


class CrousLyon(callbacks.Plugin):
    """Permet d’accéder aux menus des restaurants CROUS de Lyon et Saint Étienne."""
    threaded = True

    @wrap
    def list(self, irc, msg, args):
        """Ne prend pas d’argument.

        Liste les RUs supportés autrement que par leur identifiant numérique."""
        return irc.reply(format('%L', NAMES.keys()))


    @wrap([first('int', ('literal', tuple(NAMES.keys())))])
    def menus(self, irc, msg, args, id_):
        """<id>

        Renvoit le menu d’un RU, identifié par un entier."""
        id_ = NAMES.get(id_, id_)
        meals = get(id_)
        if not meals:
            irc.error('Aucun menu trouvé.', Raise=True)
        replies = [format('\x02%s\x02: %L', *x) for x in meals[0:2]]
        irc.replies(replies)


Class = CrousLyon


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
