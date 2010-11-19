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

import sys
import time
import threading
import BaseHTTPServer
import WebStats.templates as templates
import supybot.world as world
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.i18n as i18n
from supybot.i18n import PluginInternationalization, internationalizeDocstring
_ = PluginInternationalization('WebStats')

class TemplateOpeningError(Exception):
    pass


def getTemplate(name):
    if sys.modules.has_key('WebStats.templates.%s' % name):
        reload(sys.modules['WebStats.templates.%s' % name])
    module = __import__('WebStats.templates.%s' % name)
    print repr(module)
    return module

htmlPages = {}


class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        if not htmlPages.has_key(s.path):
            s.send_response(404)
            s.send_header("Content-type", "text/html")
            s.end_headers()
            s.wfile.write(templates.error404.get())

class Server:
    def __init__(self, plugin):
        self.serve = True
        self._plugin = plugin
    def run(self):
        serverAddress = (self._plugin.registryValue('server.host'),
                          self._plugin.registryValue('server.port'))
        httpd = BaseHTTPServer.HTTPServer(serverAddress, HTTPHandler)
        while self.serve:
            httpd.handle_request()
        httpd.server_close()
        time.sleep(1) # Let the socket be really closed


@internationalizeDocstring
class WebStats(callbacks.Plugin):
    """Add the help for "@plugin help WebStats" here
    This should describe *how* to use this plugin."""
    def __init__(self, irc):
        self.__parent = super(WebStats, self)
        callbacks.Plugin.__init__(self, irc)
        self._server = Server(self)
        if not world.testing:
            threading.Thread(target=self._server.run,
                             name="WebStats HTTP Server").start()

    def die(self):
        self._server.serve = False
        self.__parent.die()



Class = WebStats


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
