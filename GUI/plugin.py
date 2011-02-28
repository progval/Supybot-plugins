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
import hashlib
import threading
import SocketServer
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.commands as commands
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('GUI')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x
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
        def hash_(data):
            return hashlib.sha1(str(time.time()) + data).hexdigest()
        self.request.settimeout(0.5)
        currentLine = ''
        prefix = 'a%s!%s@%s.supybot-gui' % tuple([hash_(x)[0:6] for x in 'abc'])
        while self.server.enabled:
            if not '\n' in currentLine:
                try:
                    data = self.request.recv(4096)
                except socket.timeout:
                    time.sleep(0.1) # in case of odd problem
                    continue
            if not data: # Server closed connection
                return
            if '\n' in data:
                splitted = (currentLine + data).split('\n')
                currentLine = splitted[0]
                nextLines = '\n'.join(splitted[1:])
            else:
                continue
            splitted = currentLine.split(': ')
            hash_, command = splitted[0], ': '.join(splitted[1:])

            tokens = callbacks.tokenize(command)
            fakeIrc = FakeIrc(self.server._irc)
            msg = ircmsgs.privmsg(self.server._irc.nick, currentLine, prefix)
            self.server._plugin.Proxy(fakeIrc, msg, tokens)

            self.request.send('%s: %s\n' % (hash_, fakeIrc.message))
            currentLine = nextLines


class GUI(callbacks.Plugin):
    threaded  = True
    def __init__(self, irc):
        self.__parent = super(GUI, self)
        callbacks.Plugin.__init__(self, irc)
        host = self.registryValue('host')
        port = self.registryValue('port')
        while True:
            try:
                self._server = ThreadedTCPServer((host, port),
                                                 RequestHandler)
                break
            except socket.error: # Address already in use
                time.sleep(1)
        self._server.timeout = 0.5

        # Used by request handlers:
        self._server._irc = irc
        self._server._plugin = self
        self._server.enabled = True

        threading.Thread(target=self._server.serve_forever,
                         name='GUI server').start()

    def die(self):
        self.__parent.die()
        self._server.enabled = False
        time.sleep(1)
        self._server.shutdown()
        del self._server



Class = GUI


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
