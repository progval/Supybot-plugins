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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import local.lib as lib
reload(lib)
from local.lib import Citizen, Stats, Vojnik, Ekonomija
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('ERepublik')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

def getCitizen(irc, name, cls=Citizen):
    citizen = cls().loadByName(name)
    if citizen is None:
        citizen = Citizen().loadById(name)
    if citizen is None:
        irc.error(_('This citizen does not exist.'))
        return None
    return citizen

class ERepublik(callbacks.Plugin):
    threaded = True

    @internationalizeDocstring
    def info(self, irc, msg, args, name):
        """<name|id>

        Displays informations on the given citizen."""
        citizen = getCitizen(irc, name)
        if citizen is None:
            return
        string = citizen.toString()
        if string is None:
            irc.error(_('This citizen does not exist.'))
        irc.reply(string)
    info = wrap(info, ['text'])

    @internationalizeDocstring
    def medals(self, irc, msg, args, name):
        """<name|id>

        Displays the citizen's medals."""
        citizen = getCitizen(irc, name)
        if citizen is None:
            return
        irc.reply(_('%s has the following medal(s): %s') %
                  (name, citizen.getMedals()))
    medals = wrap(medals, ['text'])

    @internationalizeDocstring
    def see(self, irc, msg, args, name):
        """<name|id>

        Displays informations on the given citizen."""
        citizen = getCitizen(irc, name)
        if citizen is None:
            return
        string = citizen.toString3()
        if string is None:
            irc.error(_('This citizen does not exist.'))
        irc.reply(string)
    see = wrap(see, ['text'])

    @internationalizeDocstring
    def money(self, irc, msg, args, name):
        """<name>

        Displays money's rates."""
        money = Ekonomija().loadByName(name)
        money.toString0 = money.toString
        output = []
        units = ('gold roon brl frf dem huf cny esp cad usd gbp pln rub '
                'bgn try grd idriep irr sit pkr hrk').upper().split(' ')
        for id, unit in enumerate(units):
            output.append('%s \x02%s\x02' % (getattr(money, 'toString%i' % id)(),
                                     unit))
        irc.reply(_(', ').join(output))
    money = wrap(money, ['text'])

    @internationalizeDocstring
    def invasion(self, irc, msg, args, channel):
        """<channel>

        Calls for invasion of the channel."""

        irc.reply(_('PREPARE FOR ORGANIZED JUMP INTO THE CHANNEL'),
                  prefixNick=False)
        for i in range(0, 11):
            irc.reply('%i' % (10-i), prefixNick=False)
        irc.reply(_('Join %s !') % channel, prefixNick=False)
    invasion = wrap(invasion, ['validChannel'])

    @internationalizeDocstring
    def link(self, irc, msg, args, name):
        """<user|id>

        Returns the link to the user's profile."""
        citizen = getCitizen(irc, name)
        if citizen is None:
            return
        irc.reply('http://www.erepublik.com/en/citizen/profile/%i' %
                  citizen.getId())
    link = wrap(link, ['text'])

    @internationalizeDocstring
    def donate(self, irc, msg, args, name):
        """<user|id>

        Returns the link to the user's 'donate' page."""
        citizen = getCitizen(irc, name)
        if citizen is None:
            return
        irc.reply('http://www.erepublik.com/en/citizen/donate/items/%i' %
                  citizen.getId())
    donate = wrap(donate, ['text'])

    @internationalizeDocstring
    def menu(self, irc, msg, args):
        """take no arguments

        Returns the eRepublik main links."""
        links = {'Q5 RIFLES': 'vti-iv-a-weapon-q5/210268',
                 'Q5 Helici': 'skorpioni-avijacija/237552',
                 'Q5 Artiljerija': 'skorpionska-artiljerija1/192952'}
        for link in links:
            irc.reply('http://economy.erepublik.com/en/company/%s' % link)
    menu = wrap(menu, [])

    @internationalizeDocstring
    def land(self, irc, msg, args):
        """take no arguments

        Returns the eRepublik land links."""
        links = {'Q1 Iron Rusija': 'vti-iv-iron/193927',
                 'Q1 Iron Srbija': 'skorpijice-zelezara/222353',
                 'Q1 Titanijum Rusija': 'skorpioni-titanijum/237601'}
        for link in links:
            irc.reply('http://economy.erepublik.com/en/company/%s' % link)
    land = wrap(land, [])

    @internationalizeDocstring
    def fight(self, irc, msg, args, name):
        """<name|id>

        Shows how many damages you can make in one hit."""
        citizen = getCitizen(irc, name)
        if citizen is None:
            return
        irc.reply(_('damages: %i') % citizen.fightCalcStr(100.0))

    @internationalizeDocstring
    def kamikaze(self, irc, msg, args, name):
        """<name|id>

        Shows how many damages you can make in one hit."""
        citizen = getCitizen(irc, name)
        if citizen is None:
            return
        irc.reply(_('kamikaze attack with full food: %i') %
                  citizen.fightCalcStr(100.0))

ERepublik = internationalizeDocstring(ERepublik)
Class = ERepublik


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
