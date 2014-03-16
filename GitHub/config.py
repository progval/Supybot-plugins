###
# Copyright (c) 2011, Valentin Lorentz
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
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('GitHub')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('GitHub', True)


GitHub = conf.registerPlugin('GitHub')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(GitHub, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))
conf.registerGroup(GitHub, 'api')
conf.registerGlobalValue(GitHub.api, 'url',
        registry.String('https://api.github.com', _("""The URL of the
        GitHub API to use. You probably don't need to edit it, but I let it
        there, just in case.""")))
conf.registerGlobalValue(GitHub, 'announces',
        registry.String('', _("""You shouldn't edit this configuration
        variable yourself, unless you know what you do. Use '@Github announce
        add' or '@Github announce remove' instead.""")))

conf.registerGroup(GitHub, 'format')
conf.registerChannelValue(GitHub.format, 'push',
        registry.String('echo ' +
        _('$repository__owner__name/\x02$repository__name\x02 '
        '(in \x02$ref__branch\x02): $__commit__author__name committed '
        '\x02$__commit__message__firstline\x02 $__commit__url__tiny') \
        .replace('\n        ', ' '),
        _("""Format for push events.""")))

for event_type in ('commit_comment', 'create', 'delete', 'deployment',
        'deployment_status', 'download', 'follow', 'fork', 'fork_apply',
        'gist', 'gollum', 'issue_comment', 'issues', 'member', 'public',
        'pull_request', 'pull_request_review_comment', 'push', 'release',
        'status', 'team_add', 'watch'):
    if event_type == 'push':
        continue
    conf.registerChannelValue(GitHub.format, event_type,
            registry.String('', _("""Format for %s events.""") % event_type))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
