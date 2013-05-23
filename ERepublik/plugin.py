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

from string import Template

import supybot.conf as conf
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

def flatten_subdicts(dicts, flat={}):
    """Change dict of dicts into a dict of strings/integers. Useful for
    using in string formatting."""
    if not isinstance(dicts, dict):
        return dicts

    for key, value in dicts.items():
        if isinstance(value, dict):
            value = dict(flatten_subdicts(value))
            for subkey, subvalue in value.items():
                flat['%s__%s' % (key, subkey)] = subvalue
        else:
            flat[key] = value
    return flat

class ERepublik(callbacks.Plugin):
    threaded = True


    ##############################################################
    # Battle
    ##############################################################

    class battle(callbacks.Commands):
        def _get(self, irc, name):
            key = conf.supybot.plugins.ERepublik.apikey()
            if not key:
                irc.error(_('No API key set. Ask the owner to add one.'),
                        Raise=True)
            try:
                base = 'http://api.erpk.org/battle/%s.json?key=%s'
                data = json.load(utils.web.getUrlFd(base % (name, key)))
                return data
            except:
                irc.error(_('This battle does not exist.'), Raise=True)

        def _advinfo(self, irc, msg, args, format_, name):
            """<format> <id>

            Returns informations about a battle with advanced formating."""
            battle = flatten_subdicts(self._get(irc, name))
            repl = lambda x:Template(x).safe_substitute(battle)
            irc.replies(map(repl, format_.split('\\n')))
        advinfo = wrap(_advinfo, ['something', 'int'])

        def active(self, irc, msg, args):
            """takes no arguments

            Returns list of active battles."""
            key = conf.supybot.plugins.ERepublik.apikey()
            base = 'http://api.erpk.org/battle/active.json?key=%s'
            data = json.load(utils.web.getUrlFd(base % key))
            irc.reply(format('%L', map(str, data)))
        active = wrap(active)

        def calc(self, irc, msg, args, name):
            """<name|id>

            Calculates how many damages you can make in one hit."""
            citizen = ERepublik.citizen()._get(irc, name)
            rank = citizen['rank']['level']
            strength = citizen['strength']
            dmg = (((float (rank-1) / 20) + 0.3) * ((strength / 10) +40))
            format_ = 'Q%i: \x02%i\x02'
            irc.reply(', '.join(map(lambda x: format_ % (x, dmg*(1+(0.2*x))),
                xrange(0, 8))))
        calc = wrap(calc, ['text'])


        def _gen(format_, name, doc):
            format_ = re.sub('[ \n]+', ' ', format_)
            def f(self, irc, msg, args, *ids):
                self._advinfo(irc, msg, args, format_, *ids)
            f.__doc__ = """<id>

            %s""" % doc
            return wrap(f, ['int'], name=name)

    ##############################################################
    # Citizen
    ##############################################################

    class citizen(callbacks.Commands):
        def _get(self, irc, name):
            key = conf.supybot.plugins.ERepublik.apikey()
            if not key:
                irc.error(_('No API key set. Ask the owner to add one.'),
                        Raise=True)
            try:
                if name.isdigit():
                    base = 'http://api.erpk.org/citizen/profile/%s.json?key=%s'
                    data = json.load(utils.web.getUrlFd(base % (name, key)))
                    color = 3 if data['online'] else 4
                    data['name'] = '\x030%i%s\x0f' % (color, data['name'])
                    return data
                else:
                    base = 'http://api.erpk.org/citizen/search/%s/1.json?key=%s'
                    data = json.load(utils.web.getUrlFd(base % (name, key)))
                    return self._get(irc, str(data[0]['id']))
            except:
                irc.error(_('This citizen does not exist.'), Raise=True)

        def _advinfo(self, irc, msg, args, format_, name):
            """<format> <name|id>

            Returns informations about a citizen with advanced formating."""
            citizen = flatten_subdicts(self._get(irc, name), flat={
                    'party__name': 'None',
                    'party__id': 0,
                    'party__role': 'N/A',
                    'army__name': 'None',
                    'army__id': 0,
                    'army__role': 'N/A',
                    })
            repl = lambda x:Template(x).safe_substitute(citizen)
            irc.replies(map(repl, format_.split('\\n')))
        advinfo = wrap(_advinfo, ['something', 'text'])

        def _gen(format_, name, doc):
            format_ = re.sub('[ \n]+', ' ', format_)
            def f(self, irc, msg, args, *ids):
                self._advinfo(irc, msg, args, format_, *ids)
            f.__doc__ = """<name|id>

            %s""" % doc
            return wrap(f, ['text'], name=name)

        info = _gen("""\x02Name: $name (ID:\x0310 $id\x03)\x0310,\x03 Level: \x0310$level,\x03 Strength:\x0310 $strength,\x03 Residence:
        \x0310$residence__region__name, $residence__country__name,\x03 Citizenship:
        \x0310$citizenship__name,\x03 Rank: \x0310$rank__name,\x03 Party: \x0310$party__name,\x03 MU:
        \x0310$army__name.
        """,
        'info',
        'Returns general informations about a citizen.')

        link = _gen("""\x02$name's link\x0310 <->\x03 http://www.erepublik.com/sq/citizen/profile/$id    """,
        'link',
        'Returns link informations about a citizen.')

        donate = _gen("""\x02$name's donate link\x0310 <->\x03 http://www.erepublik.com/sq/economy/donate-items/$id    """,
        'donate',
        'Returns link to danate.')

        avatar = _gen("""\x02$name's avatar link\x0310 <->\x03 $avatar    """,
        'avatar',
        'Returns avatar link of citizen.')

        @internationalizeDocstring
        def medals(self, irc, msg, args, name):
            """<name|id>

            Displays the citizen's medals."""
            citizen = self._get(irc, name)
            medals = ['%s (%i)' % x for x in citizen['medals'].items() if x[1]]
            irc.reply(_('%s has the following medal(s): %s') %
                      (name, ', '.join(medals)))
        medals = wrap(medals, ['text'])


    ##############################################################
    # Country
    ##############################################################

    class country(callbacks.Commands):
        def _get(self, irc, name):
            key = conf.supybot.plugins.ERepublik.apikey()
            if not key:
                irc.error(_('No API key set. Ask the owner to add one.'),
                        Raise=True)
            try:
                base = 'http://api.erpk.org/country/%s/%s.json?key=%s'
                data = json.load(utils.web.getUrlFd(base %
                    (name, 'economy', key)))
                data.update(json.load(utils.web.getUrlFd(base %
                    (name, 'society', key))))
                return data
            except:
                irc.error(_('This country does not exist.'), Raise=True)

        def _advinfo(self, irc, msg, args, format_, name):
            """<format> <code>

            Returns informations about a country with advanced formating."""
            country = flatten_subdicts(self._get(irc, name))
            repl = lambda x:Template(x).safe_substitute(country)
            irc.replies(map(repl, format_.split('\\n')))
        advinfo = wrap(_advinfo, ['something', 'something'])

        def _gen(format_, name, doc):
            format_ = re.sub('[ \n]+', ' ', format_)
            def f(self, irc, msg, args, *ids):
                self._advinfo(irc, msg, args, format_, *ids)
            f.__doc__ = """<code>

            %s""" % doc
            return wrap(f, ['something'], name=name)


    ##############################################################
    # Job market
    ##############################################################

    class jobmarket(callbacks.Commands):
        def _get(self, irc, country, page):
            page = page or 1
            key = conf.supybot.plugins.ERepublik.apikey()
            if not key:
                irc.error(_('No API key set. Ask the owner to add one.'),
                        Raise=True)
            try:
                base = 'http://api.erpk.org/jobmarket/%s.json?key=%s'
                ids = '/'.join((country, page))
                data = json.load(utils.web.getUrlFd(base % (ids, key)))
                return data
            except:
                irc.error(_('This job market does not exist.'), Raise=True)

        def _advinfo(self, irc, msg, args, format_,
                country, industry, quality, page):
            """<format> <country> [<page>]

            Returns informations about a job market with advanced formating."""
            jobmarket = flatten_subdicts(self._get(irc, name))
            repl = lambda x:Template(x).safe_substitute(jobmarket)
            irc.replies(map(repl, format_.split('\\n')))
        advinfo = wrap(_advinfo, ['something', 'something', optional('int')])

        def _gen(format_, name, doc):
            format_ = re.sub('[ \n]+', ' ', format_)
            def f(self, irc, msg, args, *ids):
                self._advinfo(irc, msg, args, format_, *ids)
            f.__doc__ = """<format> <country> [<page>]

            %s""" % doc
            return wrap(f, ['something', optional('int')], name=name)


    ##############################################################
    # Market
    ##############################################################

    class market(callbacks.Commands):
        def _get(self, irc, country, industry, quality, page):
            page = page or 1
            key = conf.supybot.plugins.ERepublik.apikey()
            if not key:
                irc.error(_('No API key set. Ask the owner to add one.'),
                        Raise=True)
            try:
                base = 'http://api.erpk.org/market/%s.json?key=%s'
                ids = '/'.join((country, industry, quality, page))
                data = json.load(utils.web.getUrlFd(base % (ids, key)))
                return data
            except:
                irc.error(_('This market does not exist.'), Raise=True)

        def _advinfo(self, irc, msg, args, format_,
                country, industry, quality, page):
            """<format> <country> <industry> <quality> [<page>]

            Returns informations about a market with advanced formating."""
            market = flatten_subdicts(self._get(irc, name))
            repl = lambda x:Template(x).safe_substitute(market)
            irc.replies(map(repl, format_.split('\\n')))
        advinfo = wrap(_advinfo, ['something', 'something', 'something',
            'int', optional('int')])

        def _gen(format_, name, doc):
            format_ = re.sub('[ \n]+', ' ', format_)
            def f(self, irc, msg, args, *ids):
                self._advinfo(irc, msg, args, format_, *ids)
            f.__doc__ = """<format> <country> <industry> <quality> [<page>]

            %s""" % doc
            return wrap(f, ['something', 'something', 'int', optional('int')],
                    name=name)


    ##############################################################
    # Mu
    ##############################################################

    class mu(callbacks.Commands):
        def _get(self, irc, name):
            key = conf.supybot.plugins.ERepublik.apikey()
            if not key:
                irc.error(_('No API key set. Ask the owner to add one.'),
                        Raise=True)
            try:
                base = 'http://api.erpk.org/mu/%s.json?key=%s'
                data = json.load(utils.web.getUrlFd(base % (name, key)))
                return data
            except:
                irc.error(_('This Military Unit does not exist.'), Raise=True)

        def _advinfo(self, irc, msg, args, format_, name):
            """<format> <id>

            Returns informations about a Military Unit with advanced formating."""
            mu = flatten_subdicts(self._get(irc, name))
            repl = lambda x:Template(x).safe_substitute(mu)
            irc.replies(map(repl, format_.split('\\n')))
        advinfo = wrap(_advinfo, ['something', 'int'])

        def _gen(format_, name, doc):
            format_ = re.sub('[ \n]+', ' ', format_)
            def f(self, irc, msg, args, *ids):
                self._advinfo(irc, msg, args, format_, *ids)
            f.__doc__ = """<id>

            %s""" % doc
            return wrap(f, ['int'], name=name)


    ##############################################################
    # Party
    ##############################################################

    class party(callbacks.Commands):
        def _get(self, irc, name):
            key = conf.supybot.plugins.ERepublik.apikey()
            if not key:
                irc.error(_('No API key set. Ask the owner to add one.'),
                        Raise=True)
            try:
                base = 'http://api.erpk.org/party/%s.json?key=%s'
                data = json.load(utils.web.getUrlFd(base % (name, key)))
                return data
            except:
                irc.error(_('This party does not exist.'), Raise=True)

        def _advinfo(self, irc, msg, args, format_, name):
            """<format> <id>

            Returns informations about a party with advanced formating."""
            party = flatten_subdicts(self._get(irc, name))
            repl = lambda x:Template(x).safe_substitute(party)
            irc.replies(map(repl, format_.split('\\n')))
        advinfo = wrap(_advinfo, ['something', 'int'])

        def _gen(format_, name, doc):
            format_ = re.sub('[ \n]+', ' ', format_)
            def f(self, irc, msg, args, *ids):
                self._advinfo(irc, msg, args, format_, *ids)
            f.__doc__ = """<id>

            %s""" % doc
            return wrap(f, ['int'], name=name)

ERepublik = internationalizeDocstring(ERepublik)
Class = ERepublik


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
