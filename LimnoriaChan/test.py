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

class LimnoriaChanTestCase(ChannelPluginTestCase):
    plugins = ('LimnoriaChan',)

    def testFactoids(self):
        self.assertResponse('Hi, see the %%git repo!',
                'git://github.com/ProgVal/Limnoria.git',
                usePrefixChar=False)
        self.assertResponse('foobar: Hi, see the %%git-pl repo!',
                'foobar: git://github.com/ProgVal/Supybot-plugins.git',
                usePrefixChar=False)
        self.assertNoResponse('This does %%not exist', usePrefixChar=False)

        self.assertResponse('Hi, see %%commit#a234b0e at the Git repo.',
                'https://github.com/ProgVal/Limnoria/commit/a234b0e',
                usePrefixChar=False)


        

        # test is the bot's nick
        self.assertError('test: Hi, see the %%git repo!', usePrefixChar=False)
        self.assertError('Hi, see the %%git repo!')



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
