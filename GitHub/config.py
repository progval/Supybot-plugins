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
conf.registerGlobalValue(GitHub.announces, 'secret',
        registry.SpaceSeparatedSetOfStrings(set(), _("""Set of space-separated
        secret payloads used to authenticate GitHub."""), private=True))
conf.registerChannelValue(GitHub, 'max_announce_commits',
        registry.Integer(3, _("""Determines the maximum number of commits that
        will be announced for a single push. Note that if the number of commits
        is only one over the limit, it will be announced anyway instead of
        saying "1 more commit".""")))

conf.registerGroup(GitHub, 'format')
conf.registerGroup(GitHub.format, 'before')
conf.registerChannelValue(GitHub.format.before, 'push',
        registry.String('',
        _("""Format for an optional summary line before the individual commits
        in the push event.""")))

conf.registerChannelValue(GitHub.format, 'push',
        registry.String('echo ' +
        _('$repository__owner__name/\x02$repository__name\x02 '
        '(in \x02$ref__branch\x02): $__commit__author__name committed '
        '\x02$__commit__message__firstline\x02 $__commit__url__tiny') \
        .replace('\n        ', ' '),
        _("""Format for push events.""")))
conf.registerChannelValue(GitHub.format.push, 'hidden',
        registry.String('echo (+$__hidden_commits hidden commits)',
        _("""Format for the hidden commits message for push events.""")))
conf.registerChannelValue(GitHub.format, 'commit_comment',
        registry.String('echo ' +
        _('$repository__owner__login/\x02$repository__name\x02: '
        '$comment__user__login commented on '
        'commit \x02$comment__commit_id__short\x02 $comment__html_url__tiny') \
        .replace('\n        ', ' '),
        _("""Format for commit comment events.""")))
conf.registerChannelValue(GitHub.format, 'issues',
        registry.String('echo ' +
        _('$repository__owner__login/\x02$repository__name\x02: '
        '\x02$sender__login\x02 $action issue #$issue__number: '
        '\x02$issue__title\x02 $issue__html_url') \
        .replace('\n        ', ' '),
        _("""Format for issue events.""")))
conf.registerChannelValue(GitHub.format, 'issue_comment',
        registry.String('echo ' +
        _('$repository__owner__login/\x02$repository__name\x02: '
        '\x02$sender__login\x02 $action comment on issue #$issue__number: '
        '\x02$issue__title\x02 $issue__html_url__tiny') \
        .replace('\n        ', ' '),
        _("""Format for issue comment events.""")))
conf.registerChannelValue(GitHub.format, 'status',
        registry.String('echo ' +
        _('$repository__owner__login/\x02$repository__name\x02: Status '
        'for commit "\x02$commit__commit__message__firstline\x02" '
        'by \x02$commit__commit__committer__name\x02: \x02$description\x02 '
        '$target_url__tiny') \
        .replace('\n        ', ' '),
        _("""Format for status events.""")))
conf.registerChannelValue(GitHub.format, 'pull_request',
        registry.String('echo ' +
        _('$repository__owner__login/\x02$repository__name\x02: '
        '\x02$sender__login\x02 $action pull request #$number (to '
        '\x02$pull_request__base__ref\x02): \x02$pull_request__title\x02 '
        '$pull_request__html_url__tiny') \
        .replace('\n        ', ' '),
        _("""Format for pull request events.""")))
conf.registerChannelValue(GitHub.format, 'pull_request_review',
        registry.String('echo ' +
        _('$repository__owner__login/\x02$repository__name\x02: '
        '\x02$user__login\x02 reviewed pull request #$pull_request__number (to '
        '\x02$pull_request__base__ref\x02): \x02$pull_request__title\x02 '
        '$pull_request__html_url__tiny') \
        .replace('\n        ', ' '),
        _("""Format for pull request review events. This is triggered when
        a pull request review is finished. If you want to be notified about
        individual comments during a review, use the
        pull_request_review_comment event.""")))
conf.registerChannelValue(GitHub.format, 'pull_request_review_comment',
        registry.String('',
        _("""Format for pull request review comment events. This is for
        individual review comments, you probably only want to use the
        pull_request_review event to avoid clutter.""")))

# BEGIN AUTOGEN
EVENT_TYPES = (
    'check_suite',
    'content_reference',
    'create',
    'delete',
    'deploy_key',
    'deployment',
    'deployment_status',
    'download',
    'follow',
    'fork',
    'fork_apply',
    'github_app_authorization',
    'gist',
    'gollum',
    'installation',
    'installation_repositories',
    'label',
    'member',
    'membership',
    'meta',
    'milestone',
    'organization',
    'org_block',
    'page_build',
    'project_card',
    'project_column',
    'project',
    'public',
    'registry_package',
    'release',
    'repository_dispatch',
    'repository',
    'repository_import',
    'repository_vulnerability_alert',
    'security_advisory',
    'star',
    'team',
    'team_add',
    'watch',
)
# END EUTOGEN


for event_type in EVENT_TYPES:
    conf.registerChannelValue(GitHub.format, event_type,
            registry.String('', _("""Format for %s events.""") % event_type))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
