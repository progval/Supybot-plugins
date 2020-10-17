###
# Copyright (c) 2020, Valentin Lorentz
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

import dataclasses
import os.path
import re
import threading

import skpy
from skpy import Skype, SkypeGroupChat

from supybot import conf, utils, plugins, ircutils, callbacks, world, ircmsgs
from supybot.commands import *
from supybot.i18n import PluginInternationalization

_ = PluginInternationalization("SkypeRelay")


def dbPath():
    return conf.supybot.directories.conf.dirize("SkypeRelay_relays.txt")


@dataclasses.dataclass
class Relay:
    network: str
    channel: str
    skype_chat_id: str


class SkypeRelay(callbacks.Plugin):
    """Relays between IRC channels and Skype group chats"""

    threaded = True
    echoMessage = True

    _skype = None
    _relays = None
    _skype_loop_thread = None
    _skype_loop_stop = False

    def __init__(self, irc):
        self.__parent = super()
        self.__parent.__init__(irc)
        self._skype_loop_lock = threading.Lock()

    def die(self):
        self._skype_loop_stop = True
        self.__parent.die()

    def _readRelays(self):
        relays = []
        path = dbPath()

        if not os.path.isfile(path):
            return relays

        with open(path) as fd:
            for (i, line) in enumerate(fd):
                try:
                    (network, channel, skype_chat_id) = line.split()
                except ValueError:
                    self.log.error("Skipping invalid line %i in %s: %s", i, path, line)
                irc = world.getIrc(network)
                if irc is None:
                    self.log.warning("Unknown network %s", network)
                elif not irc.isChannel(channel):
                    self.log.warning("Invalid channel %s", channel)
                relays.append(Relay(network, channel, skype_chat_id))

        return relays

    def _writeRelays(self):
        if self._relays is None:
            return
        path = dbPath()
        with utils.file.AtomicFile(path) as fd:
            for relay in self._relays:
                fd.write("{network} {channel} {skype_chat_id}".format(**relay.__dict__))

    def _getRelays(self):
        if self._relays is None:
            self._relays = self._readRelays()
        return self._relays

    def _getSkype(self):
        if self._skype is None:
            username = self.registryValue("auth.username")
            password = self.registryValue("auth.password")
            if not username or not password:
                raise callbacks.Error(
                    _(
                        "Missing Skype username and/or password. "
                        "Configure them in supybot.plugins.SkypeRelay.auth.username "
                        "supybot.plugins.SkypeRelay.auth.password."
                    )
                )
            self._skype = Skype()
            self._skype.conn.liveLogin(username, password)
        return self._skype

    def _getChat(self, chat_name):
        return self._getSkype().chats[chat_name]

    class relay(callbacks.Commands):
        def getPlugin(self, irc):
            return irc.getCallback("SkypeRelay")

        @wrap(["owner", "networkIrc", "channel", "somethingWithoutSpaces"])
        def add(self, irc, msg, args, network, channel, skype_chat_id):
            """[<network>] [<channel>] <skype chat id>

            Adds a relay between <channel>@<network> and the reference Skype
            chat. <skype chat id> can be found using the "skyperelay chat
            recent" command.
            <network> and <channel> default to the current network and
            channel."""
            if not re.match("[0-9]+:[^@ ]+@.+", skype_chat_id):
                irc.errorInvalid(_("skype chat id"), Raise=True)
            relays = self.getPlugin(irc)._getRelays()
            relays.append(Relay(network.network, channel, skype_chat_id))
            self.getPlugin(irc)._writeRelays()
            irc.replySuccess()

        @wrap(["owner", "networkIrc", "channel", "somethingWithoutSpaces"])
        def remove(self, irc, msg, args, network, channel, skype_chat_id):
            """[<network>] [<channel>] <skype chat id>

            Remove a relay between <channel>@<network> and the reference Skype
            chat.
            <network> and <channel> default to the current network and
            channel."""
            relay = Relay(network.network, channel, skype_chat_id)
            relays = self.getPlugin(irc)._getRelays()
            try:
                relays.remove(relay)
            except ValueError:
                irc.error(_("This relay already does not exist."), Raise=True)
            self.getPlugin(irc)._writeRelays()
            irc.replySuccess()

        @wrap(["owner"])
        def list(self, irc, msg, args):
            """takes no arguments

            Returns a list of all relays."""
            replies = [
                "{channel}@{network} <-> {skype_chat_id}".format(**relay.__dict__)
                for relay in self.getPlugin(irc)._getRelays()
            ]
            if replies:
                irc.replies(replies)
            else:
                irc.reply(_("There are currently no configured relays."))

    class chat(callbacks.Commands):
        def getPlugin(self, irc):
            return irc.getCallback("SkypeRelay")

        @wrap(["owner"])
        def recent(self, irc, msg, args):
            """takes no arguments

            Returns the list of recent chats and their id."""
            replies = [
                format("\x02%s\x02 (%s)", chat.topic, chat.id)
                for chat in self.getPlugin(irc)._getSkype().chats.recent().values()
                if isinstance(chat, SkypeGroupChat)
            ]
            if replies:
                irc.replies(replies)
            else:
                irc.reply(
                    _("There are no recent chats. Try sending a message on Skype.")
                )

    def _skypeLoop(self):
        while not self._skype_loop_stop:
            events = self._getSkype().getEvents()
            for event in events:
                self._handleSkypeEvent(event)

    def _queueRelayedMsg(self, relay, s):
        msg = ircmsgs.privmsg(relay.channel, s)
        msg.tag("relayedMsg")
        world.getIrc(relay.network).queueMsg(msg)

    def _relaysFromChatId(self, chat_id):
        for relay in self._getRelays():
            if relay.skype_chat_id == chat_id:
                yield relay

    def _handleSkypeEvent(self, event):
        if isinstance(event, skpy.event.SkypeNewMessageEvent):
            if event.msg.userId == self._getSkype().userId:
                # That message was sent by myself; don't relay it (or it will echo all
                # messages from the IRC channel back to the IRC channel)
                return
            chat_id = event.msg.chatId
            content = utils.web.htmlToText(event.msg.content)
            for relay in self._relaysFromChatId(chat_id):
                self._queueRelayedMsg(
                    relay, format("<%s> %s", event.msg.userId, content)
                )
        elif isinstance(event, skpy.event.SkypeEditMessageEvent):
            if event.msg.userId == self._getSkype().userId:
                # That message was sent by myself; don't relay it (or it will echo all
                # messages from the IRC channel back to the IRC channel)
                return
            chat_id = event.msg.chatId
            content = utils.web.htmlToText(event.msg.content)
            for relay in self._relaysFromChatId(chat_id):
                self._queueRelayedMsg(
                    relay, format("<%s (edited)> %s", event.msg.userId, content)
                )
        elif isinstance(event, skpy.event.SkypeTypingEvent):
            pass
        elif isinstance(event, skpy.event.SkypeMessageEvent):
            chat_id = event.msg.chatId
            msg_type = event.msg.type
            if msg_type == "ThreadActivity/TopicUpdate":
                for relay in self._relaysFromChatId(chat_id):
                    self._queueRelayedMsg(
                        relay,
                        format(
                            "--- %s changed the topic to: %s",
                            event.msg.userId,
                            event.msg.topic,
                        ),
                    )
            else:
                self.log.warning("Unknown event message type: %s", msg_type)
        elif isinstance(event, skpy.event.SkypeChatMemberEvent):
            chat_id = event.chatId
            for relay in self._relaysFromChatId(chat_id):
                self._queueRelayedMsg(relay, "[chat group update]")
        else:
            self.log.warning("Unknown event: %r", event)

    def __call__(self, irc, msg):
        # first check so we don't acquire the lock needlessly. If we need it, then
        # acquire the lock and double-check.
        if (
            not self._skype_loop_stop
            and self._skype_loop_thread is None
            or not self._skype_loop_thread.is_alive()
        ):
            with self._skype_loop_lock:
                if (
                    self._skype_loop_thread is None
                    or not self._skype_loop_thread.is_alive()
                ):
                    self._skype_loop_thread = threading.Thread(target=self._skypeLoop)
                    self._skype_loop_thread.start()

        self.__parent.__call__(irc, msg)

    def _sendToSkype(self, irc, channel, s):
        for relay in self._getRelays():
            if relay.network == irc.network and relay.channel == channel:
                chat = self._getChat(relay.skype_chat_id)
                try:
                    chat.sendMsg(s)
                except skpy.core.SkypeApiException as e:
                    irc.error(_("Failed to relay message: %s") % e)

    def doPrivmsg(self, irc, msg):
        if msg.tagged("relayedMsg"):
            # That message was sent by myself; don't relay it (or it will echo all
            # messages from the Skype chat back to the Skype chat)
            return
        if ircmsgs.isAction(msg):
            self._sendToSkype(
                irc, msg.channel, f"* {msg.nick} {ircmsgs.unAction(msg)}"
            )
        else:
            self._sendToSkype(irc, msg.channel, f"<{msg.nick}> {msg.args[1]}")

    doNotice = doPrivmsg

    def doTopic(self, irc, msg):
        self._sendToSkype(
            irc, msg.channel, f"--- {msg.nick} changed the topic to: {msg.args[1]}"
        )


Class = SkypeRelay
