###
# Copyright (c) 2012, Valentin Lorentz
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

def init(f):
    def newf(self):
        self.assertNotError('site add lqdn https://projets.lqdn.fr/')
        try:
            f(self)
        finally:
            self.assertNotError('site remove lqdn')
    return newf

class RedmineTestCase(PluginTestCase):
    plugins = ('Redmine',)

    def testSite(self):
        self.assertRegexp('site list', 'No registered')
        self.assertNotError('site add lqdn https://projets.lqdn.fr/')
        self.assertResponse('site list', 'lqdn')
        self.assertNotError('site add lqdn2 https://projets.lqdn.fr/')
        self.assertRegexp('site list', 'lqdn2? and lqdn2?')
        self.assertNotError('site remove lqdn')
        self.assertResponse('site list', 'lqdn2')

    @init
    def testProjects(self):
        self.assertRegexp('projects lqdn', 'Campagnes \(campagne\), ')

    @init
    def testIssues(self):
        self.assertRegexp('issues lqdn --project campagne', '^\x02.*\x02 \(last.*\)')
        self.assertRegexp('issues lqdn --author 19', '^\x02.*\x02 \(last.*\)')
        self.assertRegexp('issues lqdn --assignee 19', '^\x02.*\x02 \(last.*\)')

    @init
    def testIssue(self):
        self.assertNotError('issue lqdn 130')
        self.assertResponse('issue lqdn 999999', 'Error: Issue not found.')

if not network:
    del RedmineTestCase

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
