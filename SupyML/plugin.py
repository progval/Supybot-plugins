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

import Queue
from xml.dom import minidom
import supybot.utils as utils
from supybot.commands import *
from supybot.irclib import IrcMsgQueue
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('SupyML')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

class FakeIrc():
    def __init__(self, irc):
        self._irc = irc
        self._message = ''
    def error(self, message):
        message = message
        self._data = message
    def reply(self, message):
        self._data = message
    def queueMsg(self, message):
        if message.command == 'PRIVMSG':
            self._data = message.args[1]
    def __getattr__(self, name):
        if name == '_data':
            return self.__dict__['_data']
        return getattr(self.__dict__['_irc'], name)

class SupyMLParser:
    def __init__(self, plugin, irc, msg, code):
        self._plugin = plugin
        self._irc = irc
        self._msg = msg
        self._code = code
        self._parse()
        
    def _run(self, code, proxify):
        tokens = callbacks.tokenize(str(code))
        if proxify:
            fakeIrc = FakeIrc(self._irc)
        else:
            fakeIrc = self._irc
        self._plugin.Proxy(fakeIrc, self._msg, tokens)
        if proxify:
            return fakeIrc._data
    
    def _parse(self):
        dom = minidom.parseString(self._code)
        return self._processDocument(dom)
    
    def _processDocument(self, dom):
        for childNode in dom.childNodes:
            if childNode.__class__ == minidom.Element:
                self._processNode(childNode, False)
                
    def _processNode(self, node, proxify=None):
        output = node.nodeName + ' '
        for childNode in node.childNodes:
            if childNode.__class__ == minidom.Text:
                output += childNode.data
            elif childNode.__class__ == minidom.Element:
                output += self._processNode(childNode, True)
        value = self._run(str(output), proxify)
        if proxify:
            return value

class SupyML(callbacks.Plugin):
    """SupyML is a plugin that read SupyML scripts.
    This scripts (Supybot Markup Language) are script written in a XML-based
    language."""
    threaded = True
    def eval(self, irc, msg, args, code):
        """<SupyML script>
        
        Executes the <SupyML script>"""
        parser = SupyMLParser(self, irc, msg, code)
        
    eval=wrap(eval, ['text'])
SupyML = internationalizeDocstring(SupyML)

Class = SupyML


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
