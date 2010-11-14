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
import time
import Queue
from xml.dom import minidom
import supybot.world as world
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

class ParseError(Exception):
    pass

class LoopError(Exception):
    pass

class LoopTypeIsMissing(Exception):
    pass

class FakeIrc():
    def __init__(self, irc):
        self._irc = irc
        self._message = ''
        self._data = ''
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
        self._parse(code)

    def _run(self, code, proxify):
        """Runs the command using Supybot engine"""
        tokens = callbacks.tokenize(str(code))
        if proxify:
            fakeIrc = FakeIrc(self._irc)
            # TODO : add nested level
        else:
            fakeIrc = self._irc
        self._plugin.Proxy(fakeIrc, self._msg, tokens)
        if proxify:
            # TODO : don't wait if the plugin is not threaded
            time.sleep(0.1)
            return fakeIrc._data

    def _parse(self, code, variables={}, proxify=False):
        """Returns a dom object from the code."""
        dom = minidom.parseString(code)
        output = self._processDocument(dom, variables, proxify)
        return output

    def _processDocument(self, dom, variables={}, proxify=False):
        """Handles the root node and call child nodes"""
        for childNode in dom.childNodes:
            if isinstance(childNode, minidom.Element):
                output = self._processNode(childNode, variables, proxify)
        return output

    def _processNode(self, node, variables, proxifyIrc=True):
        """Returns the value of an internapreted node.

        Takes an optional attribute, passed to self._run() that mean if the
        Irc object should be proxified. If it is not, the real Irc object is
        used, datas are sent to IRC, and this function will return None."""
        if isinstance(node, minidom.Text):
            return node.data
        output = node.nodeName + ' '
        for childNode in node.childNodes:
            if not repr(node) == repr(childNode.parentNode):
                continue
            if childNode.nodeName == 'loop':
                output += self._processLoop(childNode, variables)
            elif childNode.nodeName == 'if':
                output += self._processId(childNode, variables)
            elif childNode.nodeName == 'var':
                output += self._processVar(childNode, variables)
            elif childNode.nodeName == 'set':
                output += self._processSet(childNode, variables)
            else:
                output += self._processNode(childNode, variables) or ''
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
        loopType = None
        loopCond = 'false'
        loopContent = ''
        output = ''
        for childNode in node.childNodes:
            if loopType is None and childNode.nodeName not in ('while'):
                raise LoopTypeIsMissing(node.toxml())
            elif loopType is None:
                loopType = childNode.nodeName
                loopCond = childNode.toxml()
                loopCond = loopCond[len(loopType+'<>'):-len(loopType+'</>')]
            else:
                loopContent += childNode.toxml()
        if loopType == 'while':
            try:
                while utils.str.toBool(self._parse(loopCond, variables,
                                                   True).split(': ')[1]):
                    loopContent = '<echo>%s</echo>' % loopContent
                    output += self._parse(loopContent)
            except AttributeError: # toBool() failed
                pass
            except ValueError: # toBool() failed
                pass
        return output


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
