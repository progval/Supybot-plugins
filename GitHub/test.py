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

from supybot.test import *

DEFAULT_ISSUE_ANNOUNCE = '''progval/\x02Supybot-plugins\x02: \x02progval\x02
opened issue #350: \x02GitHub: Add config var for each issue/PR action\x02
https://github.com/progval/Supybot-plugins/issues/350'''.replace('\n', ' ')
ISSUE_EVENT = {
  "action": "opened",
  "issue": {
    "url": "https://api.github.com/repos/progval/Supybot-plugins/issues/350",
    "repository_url": "https://api.github.com/repos/progval/Supybot-plugins",
    "labels_url": "https://api.github.com/repos/progval/Supybot-plugins/issues/350/labels{/name}",
    "comments_url": "https://api.github.com/repos/progval/Supybot-plugins/issues/350/comments",
    "events_url": "https://api.github.com/repos/progval/Supybot-plugins/issues/350/events",
    "html_url": "https://github.com/progval/Supybot-plugins/issues/350",
    "id": 1601910470,
    "node_id": "I_kwDOAA_IP85fezbG",
    "number": 350,
    "title": "GitHub: Add config var for each issue/PR action",
    "user": {
      "login": "progval",
      "id": 406946,
      "node_id": "MDQ6VXNlcjQwNjk0Ng==",
      "avatar_url": "https://avatars.githubusercontent.com/u/406946?v=4",
      "gravatar_id": "",
      "url": "https://api.github.com/users/progval",
      "html_url": "https://github.com/progval",
      "followers_url": "https://api.github.com/users/progval/followers",
      "following_url": "https://api.github.com/users/progval/following{/other_user}",
      "gists_url": "https://api.github.com/users/progval/gists{/gist_id}",
      "starred_url": "https://api.github.com/users/progval/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/progval/subscriptions",
      "organizations_url": "https://api.github.com/users/progval/orgs",
      "repos_url": "https://api.github.com/users/progval/repos",
      "events_url": "https://api.github.com/users/progval/events{/privacy}",
      "received_events_url": "https://api.github.com/users/progval/received_events",
      "type": "User",
      "site_admin": False
    },
    "labels": [

    ],
    "state": "open",
    "locked": False,
    "assignee": None,
    "assignees": [

    ],
    "milestone": None,
    "comments": 0,
    "created_at": "2023-02-27T20:37:29Z",
    "updated_at": "2023-02-27T20:37:29Z",
    "closed_at": None,
    "author_association": "OWNER",
    "active_lock_reason": None,
    "body": "currently we need to mess with Conditional in order to do simple stuff like hide label/unlabel, and that's just awful",
    "reactions": {
      "url": "https://api.github.com/repos/progval/Supybot-plugins/issues/350/reactions",
      "total_count": 0,
      "+1": 0,
      "-1": 0,
      "laugh": 0,
      "hooray": 0,
      "confused": 0,
      "heart": 0,
      "rocket": 0,
      "eyes": 0
    },
    "timeline_url": "https://api.github.com/repos/progval/Supybot-plugins/issues/350/timeline",
    "performed_via_github_app": None,
    "state_reason": None
  },
  "repository": {
    "id": 1034303,
    "node_id": "MDEwOlJlcG9zaXRvcnkxMDM0MzAz",
    "name": "Supybot-plugins",
    "full_name": "progval/Supybot-plugins",
    "private": False,
    "owner": {
      "login": "progval",
      "id": 406946,
      "node_id": "MDQ6VXNlcjQwNjk0Ng==",
      "avatar_url": "https://avatars.githubusercontent.com/u/406946?v=4",
      "gravatar_id": "",
      "url": "https://api.github.com/users/progval",
      "html_url": "https://github.com/progval",
      "followers_url": "https://api.github.com/users/progval/followers",
      "following_url": "https://api.github.com/users/progval/following{/other_user}",
      "gists_url": "https://api.github.com/users/progval/gists{/gist_id}",
      "starred_url": "https://api.github.com/users/progval/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/progval/subscriptions",
      "organizations_url": "https://api.github.com/users/progval/orgs",
      "repos_url": "https://api.github.com/users/progval/repos",
      "events_url": "https://api.github.com/users/progval/events{/privacy}",
      "received_events_url": "https://api.github.com/users/progval/received_events",
      "type": "User",
      "site_admin": False
    },
    "html_url": "https://github.com/progval/Supybot-plugins",
    "description": "Collection of plugins for Supybot/Limnoria I wrote or forked.",
    "fork": False,
    "url": "https://api.github.com/repos/progval/Supybot-plugins",
    "forks_url": "https://api.github.com/repos/progval/Supybot-plugins/forks",
    "keys_url": "https://api.github.com/repos/progval/Supybot-plugins/keys{/key_id}",
    "collaborators_url": "https://api.github.com/repos/progval/Supybot-plugins/collaborators{/collaborator}",
    "teams_url": "https://api.github.com/repos/progval/Supybot-plugins/teams",
    "hooks_url": "https://api.github.com/repos/progval/Supybot-plugins/hooks",
    "issue_events_url": "https://api.github.com/repos/progval/Supybot-plugins/issues/events{/number}",
    "events_url": "https://api.github.com/repos/progval/Supybot-plugins/events",
    "assignees_url": "https://api.github.com/repos/progval/Supybot-plugins/assignees{/user}",
    "branches_url": "https://api.github.com/repos/progval/Supybot-plugins/branches{/branch}",
    "tags_url": "https://api.github.com/repos/progval/Supybot-plugins/tags",
    "blobs_url": "https://api.github.com/repos/progval/Supybot-plugins/git/blobs{/sha}",
    "git_tags_url": "https://api.github.com/repos/progval/Supybot-plugins/git/tags{/sha}",
    "git_refs_url": "https://api.github.com/repos/progval/Supybot-plugins/git/refs{/sha}",
    "trees_url": "https://api.github.com/repos/progval/Supybot-plugins/git/trees{/sha}",
    "statuses_url": "https://api.github.com/repos/progval/Supybot-plugins/statuses/{sha}",
    "languages_url": "https://api.github.com/repos/progval/Supybot-plugins/languages",
    "stargazers_url": "https://api.github.com/repos/progval/Supybot-plugins/stargazers",
    "contributors_url": "https://api.github.com/repos/progval/Supybot-plugins/contributors",
    "subscribers_url": "https://api.github.com/repos/progval/Supybot-plugins/subscribers",
    "subscription_url": "https://api.github.com/repos/progval/Supybot-plugins/subscription",
    "commits_url": "https://api.github.com/repos/progval/Supybot-plugins/commits{/sha}",
    "git_commits_url": "https://api.github.com/repos/progval/Supybot-plugins/git/commits{/sha}",
    "comments_url": "https://api.github.com/repos/progval/Supybot-plugins/comments{/number}",
    "issue_comment_url": "https://api.github.com/repos/progval/Supybot-plugins/issues/comments{/number}",
    "contents_url": "https://api.github.com/repos/progval/Supybot-plugins/contents/{+path}",
    "compare_url": "https://api.github.com/repos/progval/Supybot-plugins/compare/{base}...{head}",
    "merges_url": "https://api.github.com/repos/progval/Supybot-plugins/merges",
    "archive_url": "https://api.github.com/repos/progval/Supybot-plugins/{archive_format}{/ref}",
    "downloads_url": "https://api.github.com/repos/progval/Supybot-plugins/downloads",
    "issues_url": "https://api.github.com/repos/progval/Supybot-plugins/issues{/number}",
    "pulls_url": "https://api.github.com/repos/progval/Supybot-plugins/pulls{/number}",
    "milestones_url": "https://api.github.com/repos/progval/Supybot-plugins/milestones{/number}",
    "notifications_url": "https://api.github.com/repos/progval/Supybot-plugins/notifications{?since,all,participating}",
    "labels_url": "https://api.github.com/repos/progval/Supybot-plugins/labels{/name}",
    "releases_url": "https://api.github.com/repos/progval/Supybot-plugins/releases{/id}",
    "deployments_url": "https://api.github.com/repos/progval/Supybot-plugins/deployments",
    "created_at": "2010-10-29T07:41:23Z",
    "updated_at": "2023-02-05T11:26:05Z",
    "pushed_at": "2022-12-23T21:25:32Z",
    "git_url": "git://github.com/progval/Supybot-plugins.git",
    "ssh_url": "git@github.com:progval/Supybot-plugins.git",
    "clone_url": "https://github.com/progval/Supybot-plugins.git",
    "svn_url": "https://github.com/progval/Supybot-plugins",
    "homepage": "https://github.com/ProgVal/Limnoria/",
    "size": 4517,
    "stargazers_count": 106,
    "watchers_count": 106,
    "language": "Python",
    "has_issues": True,
    "has_projects": True,
    "has_downloads": True,
    "has_wiki": False,
    "has_pages": False,
    "has_discussions": False,
    "forks_count": 67,
    "mirror_url": None,
    "archived": False,
    "disabled": False,
    "open_issues_count": 59,
    "license": None,
    "allow_forking": True,
    "is_template": False,
    "web_commit_signoff_required": False,
    "topics": [
      "limnoria",
      "plugins",
      "python",
      "supybot"
    ],
    "visibility": "public",
    "forks": 67,
    "open_issues": 59,
    "watchers": 106,
    "default_branch": "master"
  },
  "sender": {
    "login": "progval",
    "id": 406946,
    "node_id": "MDQ6VXNlcjQwNjk0Ng==",
    "avatar_url": "https://avatars.githubusercontent.com/u/406946?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/progval",
    "html_url": "https://github.com/progval",
    "followers_url": "https://api.github.com/users/progval/followers",
    "following_url": "https://api.github.com/users/progval/following{/other_user}",
    "gists_url": "https://api.github.com/users/progval/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/progval/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/progval/subscriptions",
    "organizations_url": "https://api.github.com/users/progval/orgs",
    "repos_url": "https://api.github.com/users/progval/repos",
    "events_url": "https://api.github.com/users/progval/events{/privacy}",
    "received_events_url": "https://api.github.com/users/progval/received_events",
    "type": "User",
    "site_admin": False
  }
}

class GitHubTestCase(ChannelPluginTestCase):
    plugins = ('GitHub', 'Config', 'Utilities')
    def testAnnounceAdd(self):
        self.assertNotError('config supybot.plugins.GitHub.announces ""')
        self.assertNotError('github announce add #foo ProgVal Limnoria')
        self.assertResponse('config supybot.plugins.GitHub.announces',
                            'ProgVal/Limnoria | test | #foo')
        self.assertNotError('github announce add #bar ProgVal Supybot-plugins')
        self.assertResponse('config supybot.plugins.GitHub.announces',
                            'ProgVal/Limnoria | test | #foo || '
                            'ProgVal/Supybot-plugins | test | #bar')


    def testAnnounceRemove(self):
        self.assertNotError('config supybot.plugins.GitHub.announces '
                            'ProgVal/Limnoria | test | #foo || '
                            'ProgVal/Supybot-plugins | #bar')
        self.assertNotError('github announce remove #foo ProgVal Limnoria')
        self.assertResponse('config supybot.plugins.GitHub.announces',
                            'ProgVal/Supybot-plugins |  | #bar')
        self.assertNotError('github announce remove #bar '
                            'ProgVal Supybot-plugins')
        self.assertResponse('config supybot.plugins.GitHub.announces', ' ')

    def testAnnounceList(self):
        self.assertNotError('config supybot.plugins.GitHub.announces '
                            'abc/def | test | #foo || '
                            'abc/def | test | #bar || '
                            'def/ghi | test | #bar')
        self.assertRegexp('github announce list #foo', 'The following .*abc/def')
        self.assertRegexp('github announce list #bar', 'The following .*(abc/def.*def/ghi|def/ghi.*abc/def)')
        self.assertRegexp('github announce list #baz', 'No repositories')

    def testNoAnnounce(self):
        cb = self.irc.getCallback('GitHub')
        cb.announce.onPayload({'X-GitHub-Event': 'issues'}, ISSUE_EVENT)
        self.assertNoResponse(' ')

    def testDefaultAnnounce(self):
        self.assertNotError(
                'github announce add %s progval Supybot-plugins' %
                self.channel)
        try:
            cb = self.irc.getCallback('GitHub')
            cb.announce.onPayload(
                {'X-GitHub-Event': 'issues'},
                ISSUE_EVENT)
            self.assertResponse(' ', DEFAULT_ISSUE_ANNOUNCE)

            cb.announce.onPayload(
                {'X-GitHub-Event': 'issues'},
                {**ISSUE_EVENT, 'action': 'labeled'})
            self.assertResponse(
                ' ', DEFAULT_ISSUE_ANNOUNCE.replace('opened', 'labeled'))
        finally:
            self.assertNotError(
                    'github announce remove %s progval Supybot-plugins' %
                    self.channel)

    def testIgnoreIssueAction(self):
        self.assertNotError(
                'github announce add %s progval Supybot-plugins' %
                self.channel)
        try:
            with conf.supybot.plugins.GitHub.format.issues.labeled.context('ignore'):
                cb = self.irc.getCallback('GitHub')
                cb.announce.onPayload(
                    {'X-GitHub-Event': 'issues'},
                    ISSUE_EVENT)
                self.assertResponse(' ', DEFAULT_ISSUE_ANNOUNCE)

                cb.announce.onPayload(
                    {'X-GitHub-Event': 'issues'},
                    {**ISSUE_EVENT, 'action': 'labeled'})
                self.assertNoResponse(' ')
        finally:
            self.assertNotError(
                    'github announce remove %s progval Supybot-plugins' %
                    self.channel)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
