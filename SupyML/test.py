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

import time
from supybot.test import *

class SupyMLTestCase(ChannelPluginTestCase):
    plugins = ('SupyML', 'Utilities', 'Conditional', 'Math')
    config = {'commands.nested.maximum':50}
    #################################
    # Utilities
    def _getIfAnswerIsEqual(self, msg):
        time.sleep(0.1)
        m = self.irc.takeMsg()
        result = False
        while m is not None:
            if repr(m) == repr(msg):
                result=True
            m = self.irc.takeMsg()
        return result

    def testBasic(self):
        self.assertError('SupyML eval')
        self.assertResponse('SupyML eval <echo>foo</echo>', 'foo')
        msg = ircmsgs.privmsg(self.channel, '@SupyML eval ' \
            '<tell><echo>ProgVal</echo> <echo>foo</echo></tell>',
                                  prefix=self.prefix)
        self.irc.feedMsg(msg)
        answer = ircmsgs.IrcMsg(prefix="", command='NOTICE',
                        args=('ProgVal', 'test wants me to tell you: foo'))
        self.failIf(self._getIfAnswerIsEqual(answer) == False)
        self.assertResponse('SupyML eval <nne>4 5</nne>', 'true')
        self.assertResponse('SupyML eval <echo><nne>4 5</nne></echo>', 'true')

    def testNoMoreThanOneAnswer(self):
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<echo>foo</echo>'
                                '<echo>bar</echo>'
                            '</echo>',
                            'foobar')

    def testVar(self):
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<set name="foo">bar</set>'
                                '<echo>'
                                    '<var name="foo" />'
                                '</echo>'
                            '</echo>',
                            'bar')

    def testVarLifetime(self):
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<set name="foo">bar</set>'
                                '<echo>'
                                    '<var name="foo" />'
                                    'baz'
                                '</echo>'
                            '</echo>',
                            'barbaz')
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<set name="foo">bar</set>'
                                '<echo>'
                                    '<set name="foo">bar</set>'
                                    '<var name="foo" />'
                                '</echo>'
                                '<echo>'
                                    '<var name="foo" />'
                                '</echo>'
                            '</echo>',
                            'barbar')

    def testWhile(self):
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<set name="foo">4</set>'
                                '<loop>'
                                    '<while>'
                                        '<nne>'
                                            '<var name="foo" /> 5'
                                        '</nne>'
                                    '</while>'
                                    '<set name="foo">5</set>'
                                    '<echo>'
                                        'bar'
                                    '</echo>'
                                '</loop>'
                            '</echo>',
                            'bar')
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<set name="foo">3</set>'
                                '<loop>'
                                    '<while>'
                                        '<nne>'
                                            '<var name="foo" /> 5'
                                        '</nne>'
                                    '</while>'
                                    '<set name="foo">'
                                        '<calc>'
                                            '<var name="foo" /> + 1'
                                        '</calc>'
                                    '</set>'
                                    '<echo>'
                                        '<var name="foo" />'
                                    '</echo>'
                                '</loop>'
                            '</echo>',
                            '45')

    def testIf(self):
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<set name="foo">4</set>'
                                '<echo>'
                                    'foo'
                                '</echo>'
                                '<loop>'
                                    '<onceif>'
                                        '<lt>'
                                            '<var name="foo" /> 5'
                                        '</lt>'
                                    '</onceif>'
                                    '<echo>'
                                        'bar'
                                    '</echo>'
                                '</loop>'
                            '</echo>',
                            'foobar')
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<set name="foo">6</set>'
                                '<echo>'
                                    'foo'
                                '</echo>'
                                '<loop>'
                                    '<onceif>'
                                        '<lt>'
                                            '<var name="foo" /> 5'
                                        '</lt>'
                                    '</onceif>'
                                    '<echo>'
                                        'bar'
                                    '</echo>'
                                '</loop>'
                            '</echo>',
                            'foo')

    def testRange(self):
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<loop>'
                                    '<range>'
                                        '<echo>'
                                            '3'
                                        '</echo>'
                                    '</range>'
                                    '<echo>'
                                        'foo'
                                    '</echo>'
                                    '<var name="loop"/>'
                                '</loop>'
                            '</echo>',
                            'foo0foo1foo2')

    def testEach(self):
        self.assertResponse('SupyML eval '
                            '<echo>'
                                '<loop>'
                                    '<foreach>'
                                        'bar baz '
                                        '<echo>'
                                            'bat'
                                        '</echo>'
                                    '</foreach>'
                                    '<echo>'
                                        'foo'
                                    '</echo>'
                                    '<var name="loop"/>'
                                '</loop>'
                            '</echo>',
                            'foobarfoobazfoobat')

    def testRecursive(self):
        self.assertResponse('SupyML eval '
                         '<echo>'
                            'foo'
                            '<SupyML>eval '
                               '&lt;echo&gt;'
                                  'bar'
                               '&lt;/echo&gt;'
                            '</SupyML>'
                         '</echo>',
                         'foobar'
                        )

    def testNesting(self):
        self.assertNotError('SupyML eval ' +
                         '<echo>'*50+
                            'foo' +
                         '</echo>'*50
                        )
        self.assertError('SupyML eval ' +
                         '<echo>'*51+
                            'foo' +
                         '</echo>'*51
                        )
        self.assertResponse('SupyML eval <echo>foo <tell>bar baz</tell></echo>',
                'Error: This command cannot be nested. (tell bar baz)')

    def testExceptionHandling(self):
        self.assertNotError('SupyML eval '
                            '<echo>foo <catch><try><utilities>echo</utilities></try></catch></echo>'
                           )
        self.assertResponse('SupyML eval <echo><catch>'
                                        '<try><utilities>echo foo</utilities></try>'
                                        'bar'
                                    '</catch></echo>',
                'foo')
        self.assertResponse('SupyML eval <echo><catch>'
                                    '<try>bat<utilities>echo</utilities></try>'
                                    'foo <var name="catch"/> bar <var name="try"/>'
                                '</catch></echo>',
                'foo Invalid arguments for utilities.echo. bar bat')
        # warning, this must be the last test, since it generates a second output, not captured by assertError()
        self.assertError('SupyML eval '
                         '<echo>foo <utilities>echo</utilities></echo>'
                        )
    def testRaiseException(self):
        self.assertResponse('SupyML eval <catch>'
                                        '<try><echo>foo<raise>bar</raise></echo></try>'
                                        'Caught try:<var name="try"/> catch:<var name="catch"/>'
                                        '</catch>','Caught try:foo catch:bar')
        self.assertResponse('SupyML eval <raise>MyError</raise>','Error: MyError')
        self.assertError('SupyML eval <raise>MyError</raise>')

    def testSuccessAndError(self):
        self.assertResponse('SupyML eval <loop><onceif><success /></onceif>foo</loop>','foo')
        self.assertResponse('SupyML eval <loop><onceif><success>This stuff succeeded</success></onceif>foo</loop>','foo')
        self.assertResponse('SupyML eval <echo><loop><onceif><echo>This stuff succeeded</echo></onceif>foo</loop>bar</echo>','bar')
        self.assertResponse('SupyML eval <loop><onceif>1</onceif>foo</loop>','foo')
        self.assertResponse('SupyML eval <loop><onceif>true</onceif>foo</loop>','foo')
        self.assertResponse('SupyML eval <catch><try>'
                                             '<loop><onceif><raise>true</raise></onceif>foo</loop>'
                                             '</try>try:<var name="try"/> catch:<var name="catch"/></catch>'
                                ,'try: catch:true')

    def testQuotation(self):
        self.assertResponse('SupyML eval <quot><echo>foo</echo></quot>','"foo"')
        self.assertResponse('SupyML eval <echo>foo <quot><echo>bar baz</echo></quot></echo>','foo bar baz')
        self.assertResponse('SupyML eval <echo>foo <quot l="2"><echo>bar baz</echo></quot></echo>','foo "bar baz"')
        self.assertResponse('SupyML eval <utilities>last <echo>foo <quot l="2"><echo>bar baz</echo></quot></echo></utilities>','bar baz')

    def testWarnings(self):
        self.assertResponse('SupyML eval <echo>'
                                '<set name="">'
                                    'bar'
                                '</set>'
                                '<var name="" />'
                            '</echo>', 'bar')
        self.assertResponse('SupyML eval --warnings <echo>'
                                '<set name="">'
                                    'bar'
                                '</set>'
                                '<var name="" />'
                            '</echo>', 'Error: Empty variable name')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
