###
# Copyright (c) 2013, Valentin Lorentz
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

from supybot.test import *

import plugin

class SchemeTestCase(PluginTestCase):
    plugins = ('Scheme',)

    def testParse(self):
        self.assertEqual(plugin.parse_scheme('(+ 11 12)'),
                ['+', '11', '12'])
        self.assertEqual(plugin.parse_scheme('(+ 5 4)'),
                ['+', '5', '4'])
        self.assertEqual(plugin.parse_scheme('(+ 5 (* 4 6))'),
            ['+', '5', ['*', '4', '6']])
        self.assertEqual(plugin.parse_scheme('((lambda x x) 1 2 3)')[1:],
                ['1', '2', '3'])
        self.assertEqual(plugin.parse_scheme('((lambda (x y) (+ x y)) 11 12)'),
                [['lambda', ['x', 'y'], ['+', 'x', 'y']], '11', '12'])
    def testEval(self):
        self.assertResponse('scheme (+ 11 12)', '23')
        self.assertResponse('scheme (+ 5 4 2)', '11')
        self.assertResponse('scheme (+ 5 (* 5 2))', '15')

    def testLambda(self):
        self.assertResponse('scheme ((lambda x x) 1 2 3)', '(1 2 3)')
        self.assertResponse('scheme ((lambda (x y) (+ x y)) 11 12)', '23')

    def testSet(self):
        self.assertResponse('scheme (begin (set! x 42) x)', '42')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
