###
# Copyright (c) 2025, Valentin Lorentz
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


class RelayedCommandsTestCase(ChannelPluginTestCase):
    plugins = ("RelayedCommands", "Utilities")

    def _get_msg(self, prefix, relayednick="relayednick"):
        prefixChar = conf.supybot.reply.whenAddressedBy.chars.getSpecific(
            network=self.irc.network, channel=self.channel
        )()[0]
        return ircmsgs.privmsg(
            self.channel,
            "<%s> %secho hello $nick!$user@$host" % (relayednick, prefixChar),
            prefix,
        )

    def testDisabledByDefault(self):
        self.irc.feedMsg(
            self._get_msg("relaybotnick!relaybotuser@relaybothost")
        )
        response = self.irc.takeMsg()
        self.assertIsNone(response)

    def testRecognizeByNick(self):
        with conf.supybot.plugins.RelayedCommands.bots.nicks.context(
            ["relaybotnick"]
        ):
            self.irc.feedMsg(
                self._get_msg("relaybotnick!relaybotuser@relaybothost")
            )
            response = self.irc.takeMsg()
            self.assertIsNotNone(response)
            self.assertEqual(
                response.args,
                (self.channel, "hello relaybotnick!relaybotuser@relaybothost"),
            )

    def testRecognizeItself(self):
        with conf.supybot.plugins.RelayedCommands.bots.self.context(True):
            self.irc.feedMsg(self._get_msg(self.prefix))
            response = self.irc.takeMsg()
            self.assertIsNotNone(response)
            self.assertEqual(
                response.args,
                (self.channel, "hello %s" % self.prefix),
            )

    def testReplaceNickWhenRecognizeByNick(self):
        with conf.supybot.plugins.RelayedCommands.bots.nicks.context(
            ["relaybotnick"]
        ):
            with conf.supybot.plugins.RelayedCommands.replaceNick.context(
                True
            ):
                self.irc.feedMsg(
                    self._get_msg("relaybotnick!relaybotuser@relaybothost")
                )
                response = self.irc.takeMsg()
                self.assertIsNotNone(response)
                self.assertEqual(
                    response.args,
                    (
                        self.channel,
                        "hello relayednick!relaybotuser@relaybothost",
                    ),
                )

    def testReplaceNickWhenRecognizeItself(self):
        (_, user, host) = ircutils.splitHostmask(self.prefix)
        with conf.supybot.plugins.RelayedCommands.bots.self.context(True):
            with conf.supybot.plugins.RelayedCommands.replaceNick.context(
                True
            ):
                self.irc.feedMsg(self._get_msg(self.prefix))
                response = self.irc.takeMsg()
                self.assertIsNotNone(response)
                self.assertEqual(
                    response.args,
                    (
                        self.channel,
                        "hello %s"
                        % ircutils.joinHostmask("relayednick", user, host),
                    ),
                )

    def testDoNotReplaceInvalidNick(self):
        with conf.supybot.plugins.RelayedCommands.bots.nicks.context(
            ["relaybotnick"]
        ):
            with conf.supybot.plugins.RelayedCommands.replaceNick.context(
                True
            ):
                self.irc.feedMsg(
                    self._get_msg(
                        "relaybotnick!relaybotuser@relaybothost",
                        "invalid relayed nick",
                    )
                )
                response = self.irc.takeMsg()
                self.assertIsNotNone(response)
                self.assertEqual(
                    response.args,
                    (
                        self.channel,
                        "hello relaybotnick!relaybotuser@relaybothost",
                    ),
                )


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
