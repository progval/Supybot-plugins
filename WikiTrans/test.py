# -*- encoding: utf8 -*-
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

from __future__ import unicode_literals

from supybot.test import *

class WikiTransTestCase(PluginTestCase):
    plugins = ('WikiTrans',)

    def testTranslate(self):
        self.assertResponse('translate en be IRC', 'IRC')
        self.assertResponse('translate en fr IRC', 'Internet Relay Chat')

        self.assertResponse('translate en fr IRC bot', 'Robot IRC')
        self.assertResponse('translate fr en robot IRC', 'Internet Relay Chat bot')

        self.assertResponse('translate fr en Chef-d\'œuvre', 'Masterpiece')
        try:
            self.assertResponse('translate en fr Masterpiece', 'Chef-d\'œuvre')
            self.assertResponse('translate en fr Master (Doctor Who)',
                    'Le Maître (Doctor Who)')
        except AssertionError:
            self.assertResponse('translate en fr Masterpiece',
                    'Chef-d\'œuvre'.encode('utf8'))
            self.assertResponse('translate en fr Master (Doctor Who)',
                    'Le Maître (Doctor Who)'.encode('utf8'))


        self.assertRegexp('translate fi en paremmin', 'This word can\'t be found')

        self.assertError('translate fr de Supybot')
        self.assertError('translate fr en pogjoeregml')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
