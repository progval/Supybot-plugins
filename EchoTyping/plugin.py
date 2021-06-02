###
# Copyright (c) 2021, Valentin Lorentz
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

import time
from collections import defaultdict

from supybot import callbacks, ircmsgs

from supybot.i18n import PluginInternationalization

_ = PluginInternationalization("EchoTyping")


# Directly from the spec: https://ircv3.net/specs/client-tags/typing
LIFETIMES = {"paused": 30, "active": 6}
THROTTLE_TIME = 3


class EchoTyping(callbacks.Plugin):
    """Pretends to be typing whenever someone else is.
    This has no useful purpose, other than being annoying and
    an example implementation of the typing specification
    <https://ircv3.net/specs/client-tags/typing>"""

    def __init__(self, irc):
        super().__init__(irc)

        # {network: {channel: {nick: expiry}}}
        self._typing_users = defaultdict(lambda: defaultdict(dict))

        # {network: {channel: (status, last_timestamp)}
        self._typing_status = defaultdict(dict)

    def doTagmsg(self, irc, msg):
        if not msg.channel:
            return
        their_typing_status = msg.server_tags.get("+typing")
        if their_typing_status is None:
            return

        if their_typing_status == "done":
            self._user_stopped_typing(irc, msg.channel, msg.nick)
        elif their_typing_status in ("paused", "active"):
            self._typing_users[irc.network][msg.nick] = (
                time.time() + LIFETIMES[their_typing_status]
            )
            self._refresh_typing(irc, msg.channel, their_typing_status)
        else:
            self.log.error("Unknown +typing status: %r", their_typing_status)

    def _user_stopped_typing(self, irc, channel, nick):
        self._typing_users[irc.network][channel].pop(nick, None)

        self._expire_typing_users(irc.network, channel)

        if not self._typing_users[irc.network][channel]:
            # No one else is typing anymore, stop pretending to type.
            now = time.time()
            my_typing_status = self._typing_status[irc.network].pop(
                channel, None
            )
            if my_typing_status is None:
                # Nothing to do
                pass
            elif LIFETIMES[my_typing_status[0]] + my_typing_status[1] < now:
                # Already expired
                pass
            else:
                # Need to manually expire it
                irc.queueMsg(
                    ircmsgs.IrcMsg(
                        command="TAGMSG",
                        args=(channel,),
                        server_tags={"+typing": "done"},
                    )
                )

    def _expire_typing_users(self, network, channel):
        now = time.time()
        typing_users = self._typing_users[network][channel]
        for (nick, expiry) in list(typing_users.items()):
            if expiry > now:
                del typing_users[nick]

    def doPrivmsg(self, irc, msg):
        self._user_stopped_typing(irc, msg.channel, msg.nick)

    def doNotice(self, irc, msg):
        self._user_stopped_typing(irc, msg.channel, msg.nick)

    def doPart(self, irc, msg):
        self._user_stopped_typing(irc, msg.channel, msg.nick)

    def doNick(self, irc, msg):
        # transfer the 'typing' status from the old nick to the new nick
        old_nick = msg.nick
        new_nick = msg.args[0]
        for channel in msg.tagged("channels"):
            typing_users = self._typing_users[irc.network][channel]
            if old_nick in typing_users:
                typing_users[new_nick] = typing_users.pop(old_nick)

    def doQuit(self, irc, msg):
        for channel in msg.tagged("channels"):
            self._user_stopped_typing(irc.network, channel, msg.nick)

    def _refresh_typing(self, irc, channel, status):
        now = time.time()
        my_typing_status = self._typing_status[irc.network].get(channel)
        if my_typing_status is not None and (
            my_typing_status[1] >= now - THROTTLE_TIME
        ):
            # Throttled, drop this message.
            #
            # FIXME: the +typing status would be cleared at timestamp 6 if:
            # * user A is +typing=active at timestamp 0
            # * user B is +typing=active at timestamp 2
            # * then nothing happens
            #
            # but it should be cleared at timestamp 8, so we would need to
            # schedule a refresh somewhere between timestamps 3 and 6,
            # then manually clear it.
            return
        self._typing_status[irc.network][channel] = (status, now)
        irc.queueMsg(
            ircmsgs.IrcMsg(
                command="TAGMSG",
                args=(channel,),
                server_tags={"+typing": status},
            )
        )


Class = EchoTyping


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
