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
import copy
import Queue
import supybot.world as world
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
        self.warnings = []
        self._parse()
        
    def _run(self, code, proxify):
        """Runs the command using Supybot engine"""
        tokens = callbacks.tokenize(str(code))
        if proxify:
            fakeIrc = FakeIrc(self._irc)
        else:
            fakeIrc = self._irc
        self._plugin.Proxy(fakeIrc, self._msg, tokens)
        if proxify:
            return fakeIrc._data
    
    def _parse(self):
        """Returns a dom object from self._code."""
        dom = minidom.parseString(self._code)
        return self._processDocument(dom)

    def _processDocument(self, dom):
        """Handles the root node and call child nodes"""
        for childNode in dom.childNodes:
            if isinstance(childNode, minidom.Element):
                self._processNode(childNode, {}, False)

    def _processNode(self, node, variables, proxifyIrc=True):
        """Returns the value of an internapreted node.
        
        Takes an optional attribute, passed to self._run() that mean if the
        Irc object should be proxified. If it is not, the real Irc object is
        used, datas are sent to IRC, and this function will return None."""
        if isinstance(node, minidom.Text):
            return node.data
        output = node.nodeName + ' '
        newVariables = copy.deepcopy(variables)
        for childNode in node.childNodes:
            if not repr(node) == repr(childNode.parentNode):
                print "CONTINUING"
                continue
            if childNode.nodeName == 'loop':
                output += self._processLoop(childNode, newVariables)
            elif childNode.nodeName == 'if':
                output += self._processId(childNode, newVariables)
            elif childNode.nodeName == 'var':
                output += self._processVar(childNode, newVariables)
            elif childNode.nodeName == 'set':
                output += self._processSet(childNode, newVariables)
            else:
                output += self._processNode(childNode, newVariables) or ''
        for key in variables:
            variables[key] = newVariables[key]
        value = self._run(output, proxifyIrc)
        return value

    # Don't proxify variables
    def _processSet(self, node, variables):
        """Handles the <set> tag"""
        variableName = str(node.attributes['name'].value)
        value = ''
        for childNode in node.childNodes:
            value += self._processNode(childNode, variables)
        variables.update({variableName: value})
        return ''

    def _processVar(self, node, variables):
        """Handles the <var /> tag"""
        variableName = node.attributes['name'].value
        try:
            return variables[variableName]
        except KeyError:
            self.warnings.append('Access to non-existing variable: %s' % 
                                 variableName)
            return ''

    def _processLoop(self, node, variables):
        """Handles the <loop> tag"""
        return '<NOT IMPLEMENTED>'

    def _checkVariableName(self, variableName):
        if len(variableName) == 0:
            self.warnings.append('Empty variable name')
        if re.match('\W+', variableName):
            self.warnings.append('Variable name shouldn\'t contain '
                                 'special chars (%s)' % variableName)

class SupyML(callbacks.Plugin):
    """SupyML is a plugin that read SupyML scripts.
    This scripts (Supybot Markup Language) are script written in a XML-based
    language."""
    #threaded = True
    def eval(self, irc, msg, args, code):
        """<SupyML script>
        
        Executes the <SupyML script>"""
        parser = SupyMLParser(self, irc, msg, code)
        if world.testing and len(parser.warnings) != 0:
            print parser.warnings
        
    eval=wrap(eval, ['text'])
SupyML = internationalizeDocstring(SupyML)

Class = SupyML


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
