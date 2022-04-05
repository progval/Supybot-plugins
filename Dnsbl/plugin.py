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

import asyncio
import time
import ipaddress
from typing import Union

from supybot import utils, plugins, ircutils, callbacks, world, ircmsgs
from supybot.commands import *
from supybot.i18n import PluginInternationalization

try:
    import aiodns
    import aiodns.error
except ImportError:
    raise callbacks.Error("You have to install python3-aiodns")

_ = PluginInternationalization("Dnsbl")


async def query_provider(resolver, provider, local_part):
    try:
        results = await resolver.query(local_part + "." + provider, "A")
        return [result.host for result in results]
    except aiodns.error.DNSError as e:
        if e.args[0] == aiodns.error.ARES_ENOTFOUND:
            return ["NXDOMAIN"]
        else:
            return []


def query_providers(resolver, providers, address_str):
    try:
        address = ipaddress.ip_address(address_str)
    except ValueError:
        return []

    if address.version == 4:
        octets = str(address).split(".")
        local_part = ".".join(octets[::-1])
    else:
        assert address.version == 6, address
        local_part = ".".join(address.exploded[::-1].replace(":", ""))

    return [
        query_provider(resolver, provider, local_part)
        for provider in providers
    ]


class Dnsbl(callbacks.Plugin):
    """Bans clients connecting from hosts listed in DNS blacklists"""

    async def _should_ban_async(self, irc, msg):
        providers = self.registryValue("providers", msg.channel, irc.network)
        timeout = self.registryValue("timeout")

        deadline = time.time() + timeout
        resolver = aiodns.DNSResolver()

        pending_tasks = query_providers(resolver, providers, msg.host)
        while pending_tasks:
            (done_tasks, pending_tasks) = await asyncio.wait(
                pending_tasks,
                timeout=deadline - time.time(),
                return_when=asyncio.FIRST_COMPLETED,
            )
            for done_task in done_tasks:
                results = await done_task
                for result in results:
                    if result.startswith("127.0.0."):
                        # The host is banned; no need to wait for further results
                        resolver.cancel()
                        for pending_task in pending_tasks:
                            pending_tasks.cancel()
                        return True

        # All providers returned NXDOMAIN -> not banned
        return False

    def _should_ban(self, *args):
        return asyncio.run(self._should_ban_async(*args))

    def _handle_msg(self, irc, msg):
        if self._should_ban(irc, msg):
            irc.sendMsg(ircmsgs.ban(msg.channel, "*!*@%s" % msg.host))
            irc.sendMsg(ircmsgs.kick(msg.channel, msg.nick))

    def doJoin(self, irc, msg):
        if not self.registryValue("enable", msg.channel, irc.network):
            return
        if not msg.host:
            return
        world.SupyThread(target=self._handle_msg, args=(irc, msg)).start()


Class = Dnsbl


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=88:
