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
import collections
import getopt
import supybot.conf as conf
import supybot.log as log
from xml.dom import minidom
import supybot.world as world
import supybot.utils as utils
from supybot.commands import *
from supybot.irclib import IrcMsgQueue
import supybot.ircmsgs as ircmsgs
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

class LoopError(Exception):
    pass

class LoopTypeIsMissing(Exception):
    pass

class MaximumNodesNumberExceeded(Exception):
    pass

class SupyMLParser:
    def __init__(self, plugin, irc, msg, code, maxNodes):
        self._plugin = plugin
        self._irc = irc
        self._msg = msg
        self._code = code
        self.warnings = []
        self._maxNodes = maxNodes
        self.nodesCount = 0
        self.errors = []
        self.data = ''
        self.data += self._parse(code, variables={}, nested=irc.nested)

    def _startNode(self):
        self.nodesCount += 1
        if self.nodesCount >= self._maxNodes:
            raise MaximumNodesNumberExceeded('Script attempted to run for more iterations than currently allowed on this bot.')

    def _run(self, code, nested):
        """Runs the command using Supybot engine"""

        # New recursive engine inspired by Conditional plugin
        tokens = callbacks.tokenize(str(code))
        replies = []

        # silent variation of NestedCommandsIrcProxy
        class ErrorReportingProxy(self._plugin.Proxy):
            def reply(self2, s, *args, **kwargs):
                if ('to' in kwargs.keys()) and kwargs['to'] not in [None,'',0]:
                    return super(ErrorReportingProxy,self2).reply(s, *args, **kwargs)
                else:
                    replies.append(s)
            def replySuccess(self2, s='', **kwargs):
                v = self2._getConfig(conf.supybot.replies.success)
                if v:
                    return super(ErrorReportingProxy,self2).replySuccess(s,**kwargs)
                else:
                    # parent replySuccess() returns noReply if config is unset.
                    # however, we want something that evaluates to true for cif / onceif / while statements
                    replies.append('1')
            def error(self2, s, Raise=False, *args, **kwargs):
                if Raise:
                    raise callbacks.Error(s)
                else:
                    self.errors.append(s + ' (' + (' '.join(self2.args)) + ')')
            def _callInvalidCommands(self2):
                self.errors.append('Invalid Command (' + (' '.join(self2.args)) + ')')
            def findCallbacksForArgs(self2, args):
                # Problem; finalEval() in the proxy catches any ArgumentError exceptions from commands
                # just after calling the handler, and replies with self.reply() with a very long help string
                # if they used a self.error() everything would have been fine but like this,
                # we would end up passing this help string in a recursive context. Not good.
                # We need to inhibit the exception by overloading the command callback.

                (command, cbs) = super(ErrorReportingProxy,self2).findCallbacksForArgs(args)

                # these errors are handled with self.error() in finalEval() so all fine.
                if not cbs:
                    return (command, cbs)
                if len(cbs) > 1:
                    return (command, cbs)

                # copy the plugin object and replace the callCommand method with our wrapper.
                ocb=cbs[0]
                cb=copy.copy(ocb)
                class ErrorReportingDummyClass():
                    def callCommand(self3, command, irc, msg, *args, **kwargs):
                        try:
                            return ocb.callCommand(command, irc, msg, *args, **kwargs)
                        except (getopt.GetoptError, callbacks.ArgumentError) as e:
                            self.errors.append('Invalid arguments for ' + '.'.join(command) + '.')
                ncb = ErrorReportingDummyClass()
                cb.callCommand = ncb.callCommand

                # then return the wrapped handler
                return (command, [cb])
            def evalArgs(self2):
                # We don't want the replies in the nested command to
                # be stored here.
                super(ErrorReportingProxy, self2).evalArgs(withClass=self._plugin.Proxy)

        ErrorReportingProxy(self._irc, self._msg, tokens, nested=nested)
        return ''.join(replies)

    def _parse(self, code, variables, nested):
        """Returns a dom object from the code."""
        self._startNode()
        dom = minidom.parseString(code)
        output = self._processDocument(dom, variables, nested)
        return output

    def _processDocument(self, dom, variables, nested):
        """Handles the root node and call child nodes"""
        output = ''
        for childNode in dom.childNodes:
            if isinstance(childNode, minidom.Element):
                output += self._processNode(childNode, variables, nested)
        return output

    def _quotRecursive(self, string, level):
        # escpae backslashes and quotes
        if level>1:
            string = self._quotRecursive(string,level-1)
        string=string.replace('\\', '\\\\') #escape backslashes
        string=string.replace('"', '\\"') #escape quotes
        string='"'+string+'"' #add new quotes
        return string

    def _unescape(self, string):
        return ' '.join(callbacks.tokenize(string))

    def _processNode(self, node, variables, nested):
        """Returns the value of an interpreted node."""

        if isinstance(node, minidom.Text):
            return node.data
        if node.nodeName=='loop':
            return self._processLoop(node, variables, nested)
        if node.nodeName=='var':
            return self._processVar(node, variables)
        if node.nodeName=='set':
            return self._processSet(node, variables, nested)
        if node.nodeName=='catch':
            return self._processCatch(node, variables, nested)

        arguments = ''
        for childNode in node.childNodes:
            self._startNode()
            if not repr(node) == repr(childNode.parentNode):
                continue
            arguments += self._processNode(childNode, variables, nested + 1) or ''
        log.info("SupyML: node statement: %s"%(str(arguments)))

        if node.nodeName=='echo':
            # special handling for echo: utils echo does not like empty strings, so we reimplement
            value = self._unescape(arguments)
        elif node.nodeName=='raise':
            # raise an exception within SupyML context
            value = ''
            self.errors.append(self._unescape(arguments))
        elif node.nodeName=='quot':
            # quotes the result of the nested expression to be treated as a single token
            # until a defined number of levels up
            level = 1
            if 'l' in node.attributes.keys():
                try:
                    level=int(node.attributes['l'].value)
                except:
                    pass
                if level<1: level=1
                if level>self._maxNodes:
                    raise MaximumNodesNumberExceeded('Attempted to quote more levels than currently allowed on this bot.')
            value=self._quotRecursive(self._unescape(arguments),level)
        else:
            value = self._run(node.nodeName + ' ' + arguments, nested)

        return value

    def _processSet(self, node, variables, nested):
        """Handles the <set> tag"""
        variableName = str(node.attributes['name'].value)
        value = ''
        for childNode in node.childNodes:
            value += self._processNode(childNode, variables, nested)
        variables.update({variableName: value})
        return ''

    def _processVar(self, node, variables):
        """Handles the <var /> tag"""
        variableName = node.attributes['name'].value
        self._checkVariableName(variableName)
        try:
            return str(variables[variableName])
        except KeyError:
            self.warnings.append('Access to non-existing variable: %s'%variableName)
            return ''

    def _boolExp(self, condition, variables, nested):
        """Exception safe expression evaluation"""

        # check for errors/exceptions
        olderrors = len(self.errors)
        m = self._parse(condition, variables, nested)
        if len(self.errors)>olderrors:
            return False

        # check for success message
        v = conf.get(conf.supybot.replies.success, channel=self._msg.channel, network=self._irc.network)
        if v:
            v = ircutils.standardSubstitute(self._irc, self._msg, v)
            if len(m)>=len(v) and len(v) and (v == m[0:len(v)]):
                return True

        # check for bool
        try:
            return utils.str.toBool(m)
        except (AttributeError, ValueError):
            return False

    def _processLoop(self, node, variables, nested):
        """Handles the <loop> tag"""
        loopType = None
        loopCond = 'false'
        loopContent = ''
        output = ''
        for childNode in node.childNodes:
            if loopType is None and childNode.nodeName not in ('while','foreach','range','onceif'):
                raise LoopTypeIsMissing('Loop type is missing: '+node.toxml())
            elif loopType is None:
                loopType = childNode.nodeName
                loopCond = childNode.toxml()
                loopCond = '<echo>'+loopCond[len(loopType+'<>'):-len(loopType+'</>')]+'</echo>' # echo needed in case loopCond is empty
            else:
                loopContent += childNode.toxml()
        loopContent = '<echo>%s</echo>' % loopContent
        if loopType == 'onceif':
            if self._boolExp(loopCond, variables, nested):
                output += self._parse(loopContent, variables, nested) or ''
        if loopType == 'while':
            while self._boolExp(loopCond, variables, nested):
                output += self._parse(loopContent, variables, nested) or ''
        if loopType == 'foreach':
            tokens = callbacks.tokenize(self._parse(loopCond, variables, nested))
            for token in tokens:
                variables.update({'loop': token})
                output += self._parse(loopContent, variables, nested) or ''
        if loopType == 'range':
            try:
                left = int(self._parse(loopCond, variables, nested))
            except (AttributeError, ValueError):
                left = 0
            for token in range(left):
                variables.update({'loop': str(token)})
                output += self._parse(loopContent, variables, nested) or ''
        return output

    def _processCatch(self, node, variables, nested):
        """Handles the <catch> tag"""
        catchType = None
        catchCond = 'false'
        catchContent = ''
        for childNode in node.childNodes:
            if catchType is None and childNode.nodeName not in ('try'):
                raise LoopTypeIsMissing('<try> tag is missing: '+node.toxml())
            elif catchType is None:
                catchType = childNode.nodeName
                catchCond = childNode.toxml()
                catchCond = '<echo>'+catchCond[len(catchType+'<>'):-len(catchType+'</>')]+'</echo>' # echo needed in case catchCond is empty
            else:
                catchContent += childNode.toxml()

        # we execute the <try> part
        olderrors = len(self.errors)
        output = self._parse(catchCond, variables, nested) or ''
        newerrors = self.errors[olderrors:len(self.errors)]
        if len(newerrors)==0:
            return output

        # errors occured, we assign the error message to the catch variable and strip from global exceptions
        variables.update({'try': output})
        variables.update({'catch': ' & '.join(newerrors)})
        self.errors = self.errors[0:olderrors]
        # then execute the exception handler
        catchContent = '<echo>%s</echo>' % catchContent
        output = self._parse(catchContent, variables, nested) or ''
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
        try:
            parser = SupyMLParser(self, irc, msg, code,
                              self.registryValue('maxnodes')+2)
            errors=False
            if len(parser.errors):
                irc.error(' & '.join(parser.errors))
                errors=True
            for item in optlist:
                if ('warnings', True) == item and len(parser.warnings) != 0:
                    irc.error(' & '.join(parser.warnings))
                    errors=True
            if len(parser.data):
                irc.reply(parser.data)
            elif errors==False:
                # avoid empty result - reply success in case of silent operation with no errors
                irc.replySuccess('')
        except Exception as e:
            irc.error('SupyML script error: ' + str(e))
    eval=wrap(eval, [getopts({'warnings':''}), 'text'])

SupyML = internationalizeDocstring(SupyML)

Class = SupyML


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
