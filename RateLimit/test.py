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
import supybot.conf as conf

class RateLimitTestCase(PluginTestCase):
    plugins = ('RateLimit', 'User', 'Utilities')

    def setUp(self):
        super(RateLimitTestCase, self).setUp()
        for name in ('foo', 'bar', 'baz'):
            self.assertNotError('register %s passwd' % name,
                    frm='%s!a@a' % name)

    def testSingleUser(self):
        self.assertResponse('ratelimit get echo',
                'global: none, *: none')
        self.assertNotError('ratelimit set foo 3 1 echo')
        self.assertResponse('ratelimit get echo',
                'global: none, *: none, foo: 3 per 1 sec')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        time.sleep(1.1)
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertNoResponse('echo spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='bar!a@a')
        with conf.supybot.plugins.RateLimit.Error.context(True):
            self.assertRegexp('echo spam', 'called more than 3 times',
                    frm='foo!a@a')

        time.sleep(1.1)

        self.assertNotError('ratelimit unset foo echo')
        self.assertResponse('ratelimit get echo',
                'global: none, *: none')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')

        self.assertRegexp('ratelimit unset foo echo',
                'Error:.*did not exist')

    def testStar(self):
        self.assertResponse('ratelimit get echo',
                'global: none, *: none')
        self.assertNotError('ratelimit set * 3 1 echo')
        self.assertResponse('ratelimit get echo',
                'global: none, *: 3 per 1 sec')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertNoResponse('echo spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='bar!a@a')

    def testGlobal(self):
        self.assertResponse('ratelimit get echo',
                'global: none, *: none')
        self.assertNotError('ratelimit set 3 1 echo')
        self.assertResponse('ratelimit get echo',
                'global: 3 per 1 sec, *: none')
        self.assertResponse('echo spam', 'spam', frm='foo!a@a')
        self.assertResponse('echo spam', 'spam', frm='bar!a@a')
        self.assertResponse('echo spam', 'spam', frm='baz!a@a')
        self.assertNoResponse('echo spam', frm='foo!a@a')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
