###
# Copyright (c) 2022, Valentin Lorentz
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

# See https://datatracker.ietf.org/doc/html/draft-irtf-asrg-dnsbl#section-5
# which reserves the example addresses and domains used below


class _BaseDnsblTestCase:
    plugins = ("Dnsbl",)

    def assertKickBan(self, hostname):
        m = self._feedMsg(" ", timeout=1)
        self.assertNotEqual(m, None)
        self.assertEqual(m.command, "MODE")
        self.assertEqual(m.args, (self.channel, "+b", "*!*@" + hostname))
        m = self._feedMsg(" ")
        self.assertNotEqual(m, None)
        self.assertEqual(m.command, "KICK")

    if network:

        def testIpv4Ban(self):
            self.irc.feedMsg(
                ircmsgs.join(self.channel, prefix="foo!bar@127.0.0.2")
            )
            self.assertKickBan("127.0.0.2")

        def testIpv4Noban(self):
            self.irc.feedMsg(
                ircmsgs.join(self.channel, prefix="foo!bar@127.0.0.1")
            )
            m = self._feedMsg(" ", timeout=1)
            self.assertEqual(m, None)

        def testIpv6Ban(self):
            self.irc.feedMsg(
                ircmsgs.join(self.channel, prefix="foo!bar@::FFFF:7F00:2")
            )
            self.assertKickBan("::FFFF:7F00:2")

        def testIpv6Noban(self):
            self.irc.feedMsg(
                ircmsgs.join(self.channel, prefix="foo!bar@::FFFF:7F00:1")
            )
            m = self._feedMsg(" ", timeout=1)
            self.assertEqual(m, None)


class DnsblTestCase(_BaseDnsblTestCase, ChannelPluginTestCase):
    config = {"supybot.plugins.Dnsbl.enable": "True"}


class MultiProviderDnsblTestCase(_BaseDnsblTestCase, ChannelPluginTestCase):
    config = {
        "supybot.plugins.Dnsbl.enable": "True",
        "supybot.plugins.Dnsbl.providers": {
            "dnsbl.dronebl.org",
            "dnsbl.dronebl.org",
            "dnsbl.dronebl.org",
            "dnsbl.dronebl.org",
            "dnsbl.dronebl.org",
        },
    }


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=88:
