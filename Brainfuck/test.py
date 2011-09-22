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

from supybot.test import *

class BrainfuckTestCase(PluginTestCase):
    plugins = ('Brainfuck',)

    def testBrainfuck(self):
        self.assertResponse('brainfuck "'
                            '++++++++++[>+++++++>++++++++++>+++>+<<<<-]'
                            '>++.>+.+++++++..+++.>++.<<+++++++++++++++.'
                            '>.+++.------.--------.>+."', 'Hello World!')
        self.assertResponse('brainfuck "'
                            '++++++++++[>+++++++>++++++++++>+++>+<<<<-]'
                            '>++.>+.+++++++..+++.>++.<<+++++++++++++++.'
                            '>.+++.------.--------.>+."', 'Hello World!')

    def testInput(self):
        self.assertResponse('brainfuck --input b ",++."', 'd')
        self.assertResponse('brainfuck --input b ",,++."',
                'Error: Input too short.')

    def testTimeout(self):
        self.assertResponse('brainfuck "+[]"',
                'Error: Brainfuck processor timed out.')

    def testCheckSyntax(self):
        self.assertResponse('checksyntax "[[["',
                'Got end of string, expected `]`.')
        self.assertResponse('checksyntax "[[]"',
                'Got end of string, expected `]`.')
        self.assertResponse('checksyntax "[[]]]"',
                'Got `]` (at index 5), expected whatever you want but not that.')
        self.assertRegexp('brainfuck "[[]]]"',
                'Error: Brainfuck syntax error: .*whatever.*')

    def testRecover(self):
        self.assertNotError('brainfuck --input a ,.')
        self.assertResponse('brainfuck .', "'\\x00'")
        self.assertNotError('brainfuck --input a ,.')
        self.assertResponse('brainfuck --recover .', 'a')

    def testMemory(self):
        self.assertResponse('brainfuck <',
                'Error: Segmentation fault: Negative memory pointer.')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
