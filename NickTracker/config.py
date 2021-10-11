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

from supybot import conf, registry

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("NickTracker")
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn

    conf.registerPlugin("NickTracker", True)


NickTracker = conf.registerPlugin("NickTracker")
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(NickTracker, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))
conf.registerChannelValue(
    NickTracker,
    "targets",
    registry.SpaceSeparatedSetOfStrings(
        set(),
        _(
            """
            Space-separated list of channels and/or nicks to announce joins to.
            """
        ),
    ),
    opSettable=False,
)

conf.registerChannelValue(
    NickTracker,
    "patterns",
    registry.SpaceSeparatedListOfStrings(
        ["*!$user@$host"],
        _(
            """
            Space-separated list of patterns to use to find matches.
            For example, '$user@$host' finds all people with the same user
            and host, and '$host' finds all people with the same host.
            The following variables are available: $nick, $user, and $host.
            """
        ),
    ),
)

conf.registerGroup(NickTracker, "announce")
conf.registerGroup(NickTracker.announce, "nicks")

conf.registerChannelValue(
    NickTracker.announce.nicks,
    "lines",
    registry.PositiveInteger(
        2,
        _(
            """
            Number of lines to announce when someone joins.
            """
        ),
    ),
)

conf.registerChannelValue(
    NickTracker.announce.nicks,
    "separator",
    registry.String(
        " ",
        _(
            """
            Separator between two items in the list of nicks.
            """
        ),
    ),
)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
