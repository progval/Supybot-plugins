###
# Copyright (c) 2015, Valentin Lorentz
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


class PypySandboxTestCase(PluginTestCase):
    plugins = ('PypySandbox', 'Config')
    config = {
            'supybot.plugins.PypySandbox.timeout': 3,
            'supybot.plugins.PypySandbox.heapsize': 1000,
            }

    def testBase(self):
        self.assertResponse('sandbox print(4+5)', '9')

    def testSyntaxError(self):
        self.assertRegexp('sandbox print(4+5', 'SyntaxError')

    def testTimeout(self):
        self.assertResponse('sandbox while True: pass', 'Error: Timeout.')

    def testException(self):
        self.assertRegexp('sandbox raise ValueError("foo")',
                '.*ValueError: foo')

    def testMemory(self):
        self.assertRegexp("""sandbox "while True: """
                """s = s+'a'*10000 if 's' in locals() else ''" """,
                '.*MemoryError')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
