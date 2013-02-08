###
# Copyright (c) 2012, Valentin Lorentz
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

import requests
from BeautifulSoup import BeautifulSoup

import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.schedule as schedule
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Darkfallonline')

servers = (('US1', 'http://www.us1.darkfallonline.com/news'),
           ('EU1', 'http://www.eu1.darkfallonline.com/news'),
          )
login = 'https://ams.darkfallonline.com/AMS/'

CHANNEL = '#progval'

def check_status(url):
    up = False
    soup = BeautifulSoup(requests.get(url).text)
    status = "players"
    server = "US1"
    status = {'players': False, 'gms': False, 'mastergms': False,
            'admins': False}
     
    for img in soup.findAll('img'):
        for type_ in status:
            if img["src"].startswith("images/%s_online" % type_):
                status[type_] = True
    return status

def check_login_status(url):
    return requests.head(url).status_code == 200
    
def write_errors(f):
    def newf(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc(e)
        return
    return newf

@internationalizeDocstring
class Darkfallonline(callbacks.Plugin):
    """Add the help for "@plugin help Darkfallonline" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        super(Darkfallonline, self).__init__(irc)
        self._state = {}
        for server, url in servers:
            self._state[server] = check_status(url)
        self._login = check_login_status(login)
        schedule.addPeriodicEvent(self._announcer, 10,
                'Darkfallonline_checkstatus')
    def die(self):
        schedule.removeEvent('Darkfallonline_checkstatus')

    @write_errors
    def _announcer(self):
        for server, url in servers:
            status = self._state[server]
            new_status = check_status(url)
            for irc in world.ircs:
                if CHANNEL in irc.state.channels:
                    for type_  in new_status:
                        if new_status[type_] == status[type_]:
                            continue
                        elif new_status[type_]:
                            msg = '[%s] %s is going up' % (server,
                                    type_.capitalize())
                        else:
                            msg = '[%s] %s is going down' % (server,
                                    type_.capitalize())
                        irc.queueMsg(ircmsgs.privmsg(CHANNEL, msg))
            self._state[server] = new_status

        new_login_status = check_login_status(login)
        if new_login_status == self._login:
            pass
        elif new_login_status:
            irc.queueMsg(ircmsgs.privmsg(CHANNEL, '[login] Going up'))
        else:
            irc.queueMsg(ircmsgs.privmsg(CHANNEL, '[login] Going down'))
        self._login = new_login_status

    def status(self, irc, msg, args):
        """takes no arguments

        Return the status of all servers."""
        for server, status in self._state.items():
            irc.reply('Up on %s: %s' % (server,
                format('%L', [x.capitalize() for x,y in status.items() if y]) or 'none'),
                private=True)
        irc.reply('Login: %s' % ('on' if self._login else 'off'), private=True)

Class = Darkfallonline


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
