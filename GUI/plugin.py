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
import time
import socket
import SocketServer
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('GUI')

parseMessage = re.compile('\w+: (?P<content>.*)')
class FakeIrc:
    def __init__(self, irc):
        self.message = ''
        self._irc = irc
    def reply(self, message):
        self.message += 'Reply: %s\n' % message
    def error(self, message=''):
        self.message += 'Error: %s\n' % message
    def queueMsg(self, message):
        self._rawData = message
        if message.command in ('PRIVMSG', 'NOTICE'):
            parsed = parseMessage.match(message.args[1])
            if parsed is not None:
                message = parsed.group('content')
            else:
                message = message.args[1]
        self.message = message
    def __getattr__(self, name):
        return getattr(self.__dict__['_irc'], name)

class ThreadedTCPServer(SocketServer.TCPServer):
    pass

class RequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        currentLine = ''
        while self.server.enabled:
            if not '\n' in currentLine:
                try:
                    data = self.request.recv(4096)
                except socket.timeout:
                    continue
            if '\n' in data:
                splitted = (currentLine + data).split('\r\n')
                currentLine = splitted[0]
                nextLines = '\r\n'.join(splitted[1:])
            else:
                continue
            tokens = callbacks.tokenize(currentLine)
            fakeIrc = FakeIrc(self.server._irc)
            msg = ircmsgs.privmsg('#supybot-gui', currentLine + '\n')
            self.server._plugin.Proxy(fakeIrc, msg, tokens)
            self.request.send(fakeIrc.message)
            currentLine = nextLines


class GUI(callbacks.Plugin):
    threaded  = True
    def __init__(self, irc):
        self.__parent = super(GUI, self)
        callbacks.Plugin.__init__(self, irc)
        while True:
            try:
                self._server = ThreadedTCPServer(('127.0.0.1', 14789),
                                                 RequestHandler)
                break
            except socket.error: # Address already in use
                time.sleep(1)
        self._server._irc = irc
        self._server._plugin = self
        self._server.enabled = True

    @internationalizeDocstring
    def start(self, irc, msg, args):
        """takes no arguments

        Starts the GUI server."""
        irc.replySuccess()
        self._server.handle_request()
    start = wrap(start, [('checkCapability', 'owner')])

    @internationalizeDocstring
    def stop(self, irc, msg, args):
        """takes no arguments

        Stopss the GUI server."""
        if not hasattr(self, '_server'):
            irc.error(_('Server not enabled'))
            return
        irc.replySuccess()
    stop = wrap(stop, [('checkCapability', 'owner')])

    def __die__(self, irc):
        self.__parent = super(GUI, self)
        callbacks.Plugin.__die__(self, irc)
        self._server.enabled = False
        self._server.shutdown()
        del self._server



Class = GUI


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
