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
import supybot.world as world
import supybot.utils as utils
from supybot import httpserver
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Website')

class WebsiteCallback(httpserver.SupyHTTPServerCallback):
    name = 'Supybot website callback'
    def doPost(self, handler, path, form):
        try:
            self.plugin.announce.onPayload(form)
        except Exception as e:
            raise e
        finally:
            self.send_response(200)
            self.end_headers()

instance = None

bold = ircutils.bold

@internationalizeDocstring
class Website(callbacks.Plugin):
    """Add the help for "@plugin help Website" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        global instance
        self.__parent = super(Website, self)
        callbacks.Plugin.__init__(self, irc)
        instance = self

        callback = WebsiteCallback()
        callback.plugin = self
        httpserver.hook('website', callback)
    
    class announce(callbacks.Commands):
        matchers = {
                'id': re.compile('[a-zA-Z0-9]+'),
                'author': re.compile('[a-zA-Z0-9]+'),
                }
        def onPayload(self, form):
            for name in ('id', 'author'):
                assert self.matchers[name].match(form[name].value), \
                        '%s is not valid.' % name
            id_ = form['id'].value
            author = form['author'].value
            try:
                name = form['name'].value
            except KeyError:
                name = 'Unnamed paste'
            channel = form['channel'].value
            assert channel in ('#limnoria', '#progval')
            for irc in world.ircs:
                if irc.network == 'freenode':
                    assert channel in irc.state.channels
                    s = '%s just pasted %s: http://supybot.fr.cr/paste/%s' % (
                            bold(author),
                            bold(name),
                            id_)
                    try:
                        irc.queueMsg(ircmsgs.privmsg(channel, s))
                    except KeyError:
                        pass

    def die(self):
        self.__parent.die()
        httpserver.unhook('website')
                    
                    

Class = Website


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
