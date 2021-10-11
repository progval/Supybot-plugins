###
# Copyright (c) 2021, Valentin Lorentz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

###

from collections import defaultdict
import dataclasses
import datetime
import glob
import operator
import re
import string
import sys
import textwrap

from supybot import conf, callbacks, ircmsgs, ircutils, plugins, utils, world

from supybot.i18n import PluginInternationalization

_ = PluginInternationalization("NickTracker")


JOIN_REGEXP = re.compile(
    "(?P<date>[^ ]+)  \*\*\* "
    "(?P<nick1>[^ !]+) <(?P<nick2>[^ !]+)!(?P<user>[^@]+)@(?P<host>[^ ]+)> "
    "has joined (?P<channel>[^ ]+)\n$"
)


@dataclasses.dataclass
class Record:
    __slots__ = ("date", "nick", "user", "host")

    date: datetime.datetime
    nick: str
    user: str
    host: str


class NickTracker(callbacks.Plugin):
    """Keeps trace of the nicknames used by people connecting from the same hosts"""

    # When handling an incoming JOIN, we want to load the logs *before*
    # ChannelLogger writes them, so the current JOIN does not show up in the
    # list of past nicks.
    callBefore = ["ChannelLogger"]

    def __init__(self, irc):
        # {network: {channel: [record]}}
        super().__init__(irc)
        self._records = defaultdict(lambda: defaultdict(list))

    def _add_record(self, record, *, channel, network):
        self._records[network][channel].append(record)

    def _load_from_channellogger(self, irc, channel):
        cb = irc.getCallback("ChannelLogger")
        if not cb:
            return
        timestampFormat = conf.supybot.log.timestampFormat()
        for irc in world.ircs:
            for filename in glob.glob(cb.getLogDir(irc, channel) + "/*.log"):
                with open(filename, "rb") as fd:
                    for line in fd:
                        self._add_line(irc, timestampFormat, line)

    def _add_line(self, irc, timestampFormat, line):
        m = JOIN_REGEXP.match(line.decode(errors="replace"))
        if m:
            groups = m.groupdict()
            assert m["nick1"] == m["nick2"]
            try:
                date = datetime.datetime.strptime(m["date"], timestampFormat)
            except ValueError:
                try:
                    date = datetime.datetime.fromisoformat(m["date"])
                except ValueError:
                    self.log.error("Could not parse date: %s", m["date"])
                    return
            self._add_record(
                Record(
                    date=date,
                    nick=sys.intern(m["nick1"]),
                    user=sys.intern(m["user"]),
                    host=sys.intern(m["host"]),
                ),
                channel=m["channel"],
                network=irc.network,
            )

    def doJoin(self, irc, msg):
        if (
            msg.channel is not None
            and msg.channel not in self._records
            and msg.nick != irc.nick
        ):
            self._load_from_channellogger(irc, msg.channel)
        self._announce_join(irc, msg)
        self._add_record(
            Record(
                date=datetime.datetime.now(),
                nick=msg.nick,
                user=msg.user,
                host=msg.host,
            ),
            channel=msg.channel,
            network=irc.network,
        )

    def _announce_join(self, irc, msg):
        """Finds matching records, then calls _announce_join_to_target with the
        result for each target."""
        targets = self.registryValue("targets", msg.channel, irc.network)
        patterns = self.registryValue("patterns", msg.channel, irc.network)

        # Discard any pattern that has no variable at all.
        patterns = [
            pattern
            for pattern in patterns
            if any(var in pattern for var in ("$nick", "$user", "$host"))
        ]

        if not targets and not patterns:
            return

        patterns = [string.Template(pattern) for pattern in patterns]

        search_terms = {
            pattern.safe_substitute(
                nick=msg.nick, user=msg.user, host=msg.host
            )
            for pattern in patterns
        }

        matching_records = [
            record
            for record in self._records[irc.network][msg.channel]
            if {
                pattern.safe_substitute(dataclasses.asdict(record))
                for pattern in patterns
            }
            & search_terms
        ]
        matching_records.sort(key=operator.attrgetter("date"), reverse=True)

        nicks = {}
        for record in matching_records:
            if record.nick in nicks:
                continue
            nicks[record.nick] = record.date

        latest_nicks = [
            nick
            for (_, nick) in sorted(
                (date, nick) for (nick, date) in nicks.items()
            )
        ]

        for target in targets:
            self._announce_join_to_target(irc, msg, target, msg.channel, nicks)

    def _announce_join_to_target(self, irc, msg, target, source, nicks):
        """Announce the given list of nicks (in reverse chronological order)."""
        separator = self.registryValue(
            "announce.nicks.separator", target, irc.network
        )
        nick_string = separator.join(nicks)
        prefix = f"[{source}] {msg.nick} also used nicks: "

        # Roughly wrap to make sure it doesn't exceed 512 byte lines.
        # Assuming a reasonable no multi-byte character in the nicks,
        # this should be enough
        max_payload_size = (
            512
            - len(irc.prefix)
            - len(target)
            - len(": PRIVMSG  :\r\n")
            - len(prefix.encode())
        )
        nick_lines = utils.str.byteTextWrap(
            nick_string,
            max_payload_size - 50,  # just to be safe
        )

        max_lines = self.registryValue(
            "announce.nicks.lines", target, irc.network
        )
        nick_lines = nick_lines[0:max_lines]

        for nick_line in nick_lines:
            irc.queueMsg(
                ircmsgs.privmsg(
                    target,
                    prefix + nick_line,
                )
            )


Class = NickTracker
