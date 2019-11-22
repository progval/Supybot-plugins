###
# Copyright (c) 2019, Valentin Lorentz
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

from supybot import conf, registry
from supybot.i18n import PluginInternationalization


_ = PluginInternationalization('Apt')


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Apt', True)


Apt = conf.registerPlugin('Apt')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Apt, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))

conf.registerGroup(Apt, 'cache')
conf.registerGlobalValue(Apt.cache, 'updateInterval',
    registry.NonNegativeInteger(3600*24, _("""Minimum interval before an
    automatic update of the cache, in seconds. Set to 0 to disable automatic
    updates.""")))

conf.registerGroup(Apt, 'defaults')
conf.registerChannelValue(Apt.defaults, 'archs',
    registry.CommaSeparatedListOfStrings([], _("""Default value of --archs
    for commands that accept it. Comma-separated list of CPU architectures 
    ("arm64", "amd64", "i386", ...). """)))
conf.registerChannelValue(Apt.defaults, 'distribs',
    registry.CommaSeparatedListOfStrings([], _("""Default value of --distribs
    for commands that accept it. Comma-separated list of distributions
    ("Ubuntu", "Debian", "Debian Backports", ...). """)))
conf.registerChannelValue(Apt.defaults, 'releases',
    registry.CommaSeparatedListOfStrings([], _("""Default value of --releases
    for commands that accept it. Comma-separated list of releases ("buster",
    "bionic", "stretch", "stretch-backports", ...). """)))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
