###
# Copyright (c) 2012, Valentin Lorentz
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

import supybot.conf as conf
import supybot.registry as registry
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Redmine')

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Redmine', True)


Redmine = conf.registerPlugin('Redmine')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Redmine, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))

conf.registerGlobalValue(Redmine, 'sites',
    registry.Json({}, _("""JSON-formatted dict of site data. Don't edit
    this unless you known what you are doing. Use @site add and @site
    remove instead.""")))
conf.registerChannelValue(Redmine, 'defaultsite',
    registry.String('', _("""Default site for this channel.""")))
conf.registerGroup(Redmine, 'format')
conf.registerChannelValue(Redmine.format, 'projects',
    registry.String('%(name)s (%(identifier)s)',
    _("""Format of projects displayed by @projects.""")))
conf.registerChannelValue(Redmine.format, 'issues',
    registry.String('\x02#%(id)i: %(subject)s\x02 (last update: '
    '%(updated_on)s / status: %(status__name)s)',
    _("""Format of issues displayed by @issues.""")))
conf.registerChannelValue(Redmine.format, 'issue',
    registry.String('\x02#%(id)i (%(status__name)s)\x02: \x02%(subject)s\x02 '
    'in \x02%(project__name)s\x02 (%(project__id)i). Created by '
    '\x02%(author__name)s\x02 (%(author__id)i) on \x02%(created_on)s\x02, '
    'last updated on \x02%(updated_on)s', 
    _("""Format of issues displayed by @issue.""")))
conf.registerGroup(Redmine.format, 'announces')
conf.registerChannelValue(Redmine.format.announces, 'issue',
    registry.String('Updated issue: \x02#%(id)i (%(status__name)s)\x02: '
    '\x02%(subject)s\x02 in \x02%(project__name)s\x02 (%(project__id)i).',
    _("""Format of issues displayed by @issue.""")))

conf.registerGroup(Redmine, 'announce')
conf.registerChannelValue(Redmine.announce, 'sites',
    registry.SpaceSeparatedListOfStrings([],
    _("""List of sites announced on this channel.""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
