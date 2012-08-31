###
# Copyright (c) 2010, quantumlemur
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

import json
import time
import socket
import threading
import traceback
import supybot.log as log
import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.registry as registry
import supybot.callbacks as callbacks

from supybot.i18n import PluginInternationalization
from supybot.i18n import internationalizeDocstring
_ = PluginInternationalization('Listener')

def serialize_relay(relay):
    format_ = _('from %(host)s:%(port)s to %(channel)s@%(network)s')
    return format_ % relay

class Listener(callbacks.Plugin):
    """Add the help for "@plugin help Listener" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Listener, self)
        self.__parent.__init__(irc)
        self.listenerThreads = []
        try:
            conf.supybot.plugins.Listener.relays.addCallback(
                    self._loadFromConfig)
        except registry.NonExistentRegistryEntry:
            log.error("Your version of Supybot is not compatible with "
                      "configuration hooks. So, Listener won't be able "
                      "to reload the configuration if you use the Config "
                      "plugin.")
        self._loadFromConfig()

    def _loadFromConfig(self, name=None):
        relays = json.loads(self.registryValue('relays'))
        for thread in self.listenerThreads:
            thread.active = False
            thread.listener.close()
        time.sleep(2)
        self.listenerThreads = []
        for relay in relays:
            try:
                log.debug('Starting listener thread: %s' %
                        serialize_relay(relay))
                thread = self.ListeningThread(**relay)
                thread.start()
                self.listenerThreads.append(thread)
            except TypeError:
                irc.error('Cannot load relay: %s' % serialize_relay(relay))


    class ListeningThread(threading.Thread):
        def __init__(self, network, channel, host, port):
            threading.Thread.__init__(self)
            self.network = network
            self.channel = channel
            self.host = host
            self.port = port
            self.buffer = ''
            self.active = True
            self.listener = socket.socket()
            self.listener.settimeout(0.5)
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener.bind((self.host, self.port))
            self.listener.listen(4)

        def run(self):
            while self.active:
                try:
                    conn, addr = self.listener.accept()
                    self.buffer = conn.recv(4092).split('\n')[0].rstrip('\r')
                    conn.close()
                except IOError:
                    pass
                if self.buffer:
                    for IRC in world.ircs:
                        if IRC.network == self.network:
                            try:
                                IRC.queueMsg(ircmsgs.privmsg(self.channel, self.buffer))
                            except Exception as e:
                                traceback.print_exc(e)
                    self.buffer = ''
            self.listener.close()

    def add(self, irc, msg, args, channel, network, host, port):
        """[<channel>] [<network>] <host> <port>

        Start listening on <host>:<port> and relays messages to <channel> @
        <network>.
        <channel> and <network> default to the current ones."""
        relays = json.loads(self.registryValue('relays'))
        relay = {'channel': channel, 'network': network.network,
            'host': host, 'port': port}
        if relay in relays:
            irc.error(_('This relay already exists.'), Raise=True)
        relays.append(relay)
        self.setRegistryValue('relays', value=json.dumps(relays))
        self._loadFromConfig()
        irc.replySuccess()
    add = wrap(add, ['channel', 'networkIrc', 'somethingWithoutSpaces',
        ('int', 'port', lambda x: (x<65536))])

    def remove(self, irc, msg, args, channel, network, host, port):
        """[<channel>] [<network>] <host> <port>

        Start listening on <host>:<port> and relays messages to <channel> @
        <network>.
        <channel> and <network> default to the current ones."""
        relays = json.loads(self.registryValue('relays'))
        relay = {'channel': channel, 'network': network.network,
            'host': host, 'port': port}
        try:
            relays.remove(relay)
        except ValueError:
            irc.error(_('This relay does not exist.'), Raise=True)
        self.setRegistryValue('relays', value=json.dumps(relays))
        self._loadFromConfig()
        irc.replySuccess()
    remove = wrap(remove, ['channel', 'networkIrc', 'somethingWithoutSpaces',
        ('int', 'port', lambda x: (x<65536))])

    def list(self, irc, msg, args):
        """takes no arguments

        Return a list of all relays."""
        relays = json.loads(self.registryValue('relays'))
        irc.replies([serialize_relay(x) for x in relays])
    list = wrap(list)

    def stop(self, irc, msg, args):
        """takes no arguments

        Tries to close all listening sockets"""
        for thread in self.listenerThreads:
            thread.active = False
            thread.listener.close()
        self.listenerThreads = []
        irc.replySuccess()
    stop = wrap(stop)

    def die(self):
        for thread in self.listenerThreads:
            thread.active = False
            thread.listener.close()
        self.listenerThreads = []
        time.sleep(2)

Class = Listener


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
