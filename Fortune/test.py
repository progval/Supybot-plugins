###
# Copyright (c) 2014, Valentin Lorentz
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

import tempfile
from supybot.test import *

def with_db(f):
    def newf(self):
        with tempfile.NamedTemporaryFile('w') as fd:
            try:
                self.assertNotError('fortune database add testdb %s' % fd.name)
                f(self, fd)
            finally:
                self.assertNotError('fortune database remove testdb')
    return newf

class FortuneTestCase(PluginTestCase):
    plugins = ('Fortune',)

    @with_db
    def testRandomLength(self, fd):
        fd.write('long'*200)
        fd.write('\n')
        fd.seek(0)
        self.assertResponse('random testdb',
                'Error: No fortune matched the search.')
        fd.seek(0, 2)
        fd.write('foo\n%\nbar\n%\n')
        fd.write('long'*200)
        fd.write('\n')
        fd.seek(0)
        for x in range(0, 10):
            self.assertRegexp('random testdb', '(foo|bar)')

    @with_db
    def testLinebreak(self, fd):
        fd.write('foo\nbar\n\n%\nfoo\nbar\n')
        fd.seek(0)
        self.assertResponse('random testdb', 'foo bar')
    
    @with_db
    def testList(self, fd):
        self.assertResponse('database list', 'testdb <%s>' % fd.name)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
