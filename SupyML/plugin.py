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
import sys
import copy
import time
import supybot.conf as conf
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

class MaximumNodesNumberExceeded(Exception):
    pass

parseMessage = re.compile('\w+: (?P<content>.*)')
class FakeIrc():
    def __init__(self, irc):
        self._irc = irc
        self._message = ''
        self._data = ''
        self._rawData = None
    def error(self, message):
        message = message
        self._data = message
    def reply(self, message):
        self._data = message
    def queueMsg(self, message):
        self._rawData = message
        if message.command in ('PRIVMSG', 'NOTICE'):
            parsed = parseMessage.match(message.args[1])
            if parsed is not None:
                message = parsed.group('content')
            else:
                message = message.args[1]
        self._data = message
    def __getattr__(self, name):
        if name == '_data' or name == '_rawData':
            return self.__dict__[name]
        return getattr(self.__dict__['_irc'], name)

class SupyMLParser:
    def __init__(self, plugin, irc, msg, code, maxNodes):
        self._plugin = plugin
        self._irc = irc
        self._msg = msg
        self._code = code
        self.warnings = []
        self._maxNodes = maxNodes
        self.nodesCount = 0
        self.data = self._parse(code)

    def _startNode(self):
        self.nodesCount += 1
        if self.nodesCount >= self._maxNodes:
            raise MaximumNodesNumberExceeded()

    def _run(self, code, nested):
        """Runs the command using Supybot engine"""
        tokens = callbacks.tokenize(str(code))
        fakeIrc = FakeIrc(self._irc)
        callbacks.NestedCommandsIrcProxy(fakeIrc, self._msg, tokens,
                nested=(1 if nested else 0))
        self.rawData = fakeIrc._rawData
        # TODO : don't wait if the plugin is not threaded
        time.sleep(0.1)
        return fakeIrc._data

    def _parse(self, code, variables={}):
        """Returns a dom object from the code."""
        self._startNode()
        dom = minidom.parseString(code)
        output = self._processDocument(dom, variables)
        return output

    def _processDocument(self, dom, variables={}):
        """Handles the root node and call child nodes"""
        for childNode in dom.childNodes:
            if isinstance(childNode, minidom.Element):
                output = self._processNode(childNode, variables, nested=False)
        return output

    def _processNode(self, node, variables, nested=True):
        """Returns the value of an internapreted node."""

        if isinstance(node, minidom.Text):
            return node.data
        output = node.nodeName + ' '
        for childNode in node.childNodes:
            self._startNode()
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
        value = self._run(output, nested)
        return value

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
        self._checkVariableName(variableName)
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
                                                  ).split(': ')[-1]):
                    loopContent = '<echo>%s</echo>' % loopContent
                    output += self._parse(loopContent) or ''
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
    def eval(self, irc, msg, args, optlist, code):
        """[--warnings] <SupyML script>

        Executes the <SupyML script>"""
        parser = SupyMLParser(self, irc, msg, code,
                              self.registryValue('maxnodes')+2)
        for item in optlist:
            if ('warnings', True) == item and len(parser.warnings) != 0:
                irc.error(' & '.join(parser.warnings))
        if parser.rawData is not None:
            irc.queueMsg(parser.rawData)
        else:
            irc.reply(parser.data)

    eval=wrap(eval, [getopts({'warnings':''}), 'text'])

SupyML = internationalizeDocstring(SupyML)

Class = SupyML


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
