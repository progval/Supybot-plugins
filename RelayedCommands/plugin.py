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

import re

from supybot import utils, plugins, ircutils, callbacks, ircmsgs, ircdb, conf
from supybot.commands import *
from supybot.i18n import PluginInternationalization


_ = PluginInternationalization("RelayedCommands")

REGEXP = re.compile("^<(?P<nick>[^>]+)> (?P<message>.*)?")


class RelayedCommands(callbacks.Plugin):
    """Recognizes commands sent through a relay bot and runs them"""

    def doPrivmsg(self, irc, msg):
        if not (
            msg.nick == irc.nick
            and self.registryValue("bots.self", msg.channel, irc.network)
        ) and msg.nick not in self.registryValue(
            "bots.nicks", msg.channel, irc.network
        ):
            return

        match = REGEXP.match(msg.args[1])
        if match is None:
            return

        if msg.channel is None or callbacks.addressed(irc, msg):
            return

        prefix = msg.prefix
        if self.registryValue("replaceNick", msg.channel, irc.network):
            (nick, user, host) = ircutils.splitHostmask(prefix)
            newnick = match.group("nick")
            if ircutils.isNick(newnick, strictRfc=False):
                prefix = ircutils.joinHostmask(newnick, user, host)
            else:
                self.log.info(
                    "%r is not a valid nick; not using it as command author",
                    newnick,
                )
        newmsg = ircmsgs.IrcMsg(
            args=[msg.args[0], match.group("message")], prefix=prefix, msg=msg
        )
        newmsg.tag(
            "addressed", None
        )  # clear cache, which was copied from 'msg'

        command = callbacks.addressed(irc, newmsg)
        if command:
            if ircdb.checkIgnored(newmsg.prefix):
                self.log.info(
                    "Ignoring command relayed by bot %s.", msg.prefix
                )
                return
            if ircdb.checkIgnored(newmsg.prefix):
                self.log.info(
                    "Ignoring command from %s relayed by bot %s.",
                    match.group("nick"),
                    msg.prefix,
                )
                return

            #############################
            # Copied from Owner/plugin.py:

            Owner = irc.getCallback("Owner")
            maximum = conf.supybot.abuse.flood.command.maximum()
            Owner.commands.enqueue(newmsg)
            if (
                conf.supybot.abuse.flood.command()
                and Owner.commands.len(newmsg) > maximum
                and not ircdb.checkCapability(newmsg.prefix, "trusted")
            ):
                punishment = conf.supybot.abuse.flood.command.punishment()
                banmask = conf.supybot.protocols.irc.banmask.makeBanmask(
                    newmsg.prefix
                )
                self.log.info(
                    "Ignoring %s for %s seconds due to an apparent "
                    "command flood.",
                    banmask,
                    punishment,
                )
                ircdb.ignores.add(banmask, time.time() + punishment)
                if conf.supybot.abuse.flood.command.notify():
                    irc.reply(
                        "You've given me %s commands within the last "
                        "%i seconds; I'm now ignoring you for %s."
                        % (
                            maximum,
                            conf.supybot.abuse.flood.interval(),
                            utils.timeElapsed(punishment, seconds=False),
                        )
                    )
                return
            self.log.info(
                "Running command from %s relayed by %s",
                match.group("nick"),
                msg.prefix,
            )
            try:
                tokens = callbacks.tokenize(
                    command, channel=newmsg.channel, network=irc.network
                )
                self.Proxy(irc, newmsg, tokens)
            except SyntaxError as e:
                if conf.supybot.reply.error.detailed():
                    irc.error(str(e))
                else:
                    irc.replyError(msg=newmsg)
                    self.log.info("Syntax error: %s", e)

            #
            #############################

            if newmsg.tagged("repliedTo"):
                msg.tag("repliedTo")


Class = RelayedCommands


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
