# Limnoria GitHub plugin

This plugin announces events GitHub repositories to IRC.

**This plugin requires Limnoria.**

## Webhook Setup

To use this plugin you must forward/open the port which is specified by 
the configuration variable `supybot.servers.http.port` (8080 is the 
default value). For more information, see 
[Using the HTTP server in Limnoria's documentation](https://docs.limnoria.net/use/httpserver.html).

To add announces use the command `github announce add <owner> <repo>` 
`Owner` means the owner of the repository (GitHub username) 
and repo what git repository the bot should announce. When you want to 
remove announce, use the command `github announce remove <owner> <repo>`.

Please note that the names are case-sensitive. If you use mis-spelled 
repository names, the bot will not announce commits to that repository. Globs are
also supported in the `<owner>` and `<repo>` fields.

To get the bot notified about events, you must tell GitHub to post to your 
bot. [GitHub explanation](http://help.github.com/post-receive-hooks/)
In order to do that, you must go admin page of repo, tab webhooks 
(direct link: ` https://github.com/<owner>/<repo>/settings/hooks ` ) and 
click `Add webhook` and add the URL of your bot there. The URL is 
` http://<IP or dynamicdns-service>:<port>/github `.
Let the `Content type` be `application/json`!

**NOTE:** Previous versions of this plugin used `application/x-www-form-urlencoded`!

Fill the other fields of the form according to what you want.

## Announce format

This plugin has a default configuration to announce events most people want to
see announced on IRC, using bold formatting and no colors; but this can be tweaked.

### Syntax description

To announce other events type, you have to set config variables 
`supybot.plugins.GitHub.format.<type>` (where `type` is a type referenced 
at http://developer.github.com/webhooks/#events ) to a template.
A template is a command, where you can use @echo to print variable content.
Variable names are prefixed with a $.
Replacements will be made using the data sent by GitHub. As this data 
contains lists and dictionnaries, it is “flattened”, ie. 
`data['foo']['bar']['baz']` can be accessed with `$foo__bar__baz` (note the douple underscores).
There are also special variables:
* if `$foo` is an url, `$foo__tiny` will be the tinyfied version of the URL
* if `$foo` is a git ref, `$foo__branch` will be the matching branch
* if `$foo` is a string, `$foo__firstline` will contain the first line of 
`$foo`

Concerning push events, one line is formatted per commit; it is given extra
 variables: `$__commit__foo` for each `data['commits'][X]['foo']`.

Format of 'issues' and 'pull_request' events can be overridden on a per-action
basis, with the `supybot.plugins.GitHub.format.<type>.<action>` config variable.
Note that setting `supybot.plugins.GitHub.format.<type>.<action>` globally overrides
channel-specific values of `supybot.plugins.GitHub.format.<type>`.
For example, in order to ignore label-related actions, you can use:

```
@config supybot.plugins.GitHub.format.issues.labeled ignore
@config supybot.plugins.GitHub.format.issues.unlabeled ignore
@config supybot.plugins.GitHub.format.pull_request.labeled ignore
@config supybot.plugins.GitHub.format.pull_request.unlabeled ignore
```

The plugin can validate if the payload was sent by GitHub with a proper secret if `supybot.plugins.Github.announces.secret`
is set.

The Utilities plugin is required to be active for this plugin to work.

### Default configuration

Here are the default templates:

```
supybot.plugins.GitHub.format.issue_comment: echo $repository__owner__login/\x02$repository__name\x02: \x02$sender__login\x02 $action comment on issue #$issue__number: \x02$issue__title\x02 $comment__html_url__tiny
supybot.plugins.GitHub.format.issues: echo $repository__owner__login/\x02$repository__name\x02: \x02$sender__login\x02 $action issue #$issue__number: \x02$issue__title\x02 $issue__html_url
supybot.plugins.GitHub.format.pull_request: echo $repository__owner__login/\x02$repository__name\x02: \x02$sender__login\x02 $action pull request #$number (to \x02$pull_request__base__ref\x02): \x02$pull_request__title\x02 $pull_request__html_url__tiny
supybot.plugins.GitHub.format.pull_request_review: echo $repository__owner__login/\x02$repository__name\x02: \x02$review__user__login\x02 reviewed pull request #$pull_request__number (to \x02$pull_request__base__ref\x02): \x02$pull_request__title\x02 $pull_request__html_url__tiny
supybot.plugins.GitHub.format.pull_request_review_comment: echo $repository__owner__login/\x02$repository__name\x02: \x02$comment__user__login\x02 reviewed pull request #$pull_request__number (to \x02$pull_request__base__ref\x02): \x02$pull_request__title\x02 $pull_request__html_url__tiny
supybot.plugins.GitHub.format.pull_request_review_thread:
supybot.plugins.GitHub.format.push: echo $repository__owner__name/\x02$repository__name\x02 (in \x02$ref__branch\x02): $__commit__author__name committed \x02$__commit__message__firstline\x02 $__commit__url__tiny
supybot.plugins.GitHub.format.push.hidden: echo (+$__hidden_commits hidden commits)
supybot.plugins.GitHub.format.status: echo $repository__owner__login/\x02$repository__name\x02: Status for commit "\x02$commit__commit__message__firstline\x02" by \x02$commit__commit__committer__name\x02: \x02$description\x02 $target_url__tiny
```

everything else, and therefore is not announce

### Notifico-style configuration

Here is an alternative set of configuration values, which are more verbose, use colors and no bold,
[inspired by Notifico](https://github.com/TkTech/notifico/blob/85a84b28625d36733a2037960970d9443fd8cabc/notifico/contrib/services/github.py#L340).
They expect the Conditional plugin to be loaded.

```
supybot.plugins.GitHub.format.ping: echo "\x0F[\x0302GitHub\x0F]" $zen
supybot.plugins.GitHub.format.issues: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F $action issue \x0303#$issue__number\x0F: $issue__title - \x0313$issue__html_url\x0F
supybot.plugins.GitHub.format.issue_comment: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F $action a comment on issue \x0303#$issue__number\x0F: $issue__title - \x0313$comment__html_url\x0F
supybot.plugins.GitHub.format.commit_comment: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$comment__user__login\x0F $action a comment on commit \x0303$comment__commit_id\x0F - \x0313$comment__html_url\x0F
supybot.plugins.GitHub.format.create: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F created $ref_type \x0303$ref\x0F - \x0313$repository__html_url\x0F
supybot.plugins.GitHub.format.delete: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F deleted $ref_type \x0303$ref\x0F - \x0313$repository__html_url\x0F
supybot.plugins.GitHub.format.pull_request: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F $action pull request \x0303#$number\x0F: $pull_request__title - \x0313$pull_request__html_url\x0F
supybot.plugins.GitHub.format.pull_request_review_comment: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$comment__user__login\x0F reviewed pull request \x0303#$pull_request__number\x0F commit - \x0313$comment__html_url\x0F
supybot.plugins.GitHub.format.watch: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F starred \x0303$repository__owner__login/$repository__name\x0F - \x0313$sender__html_url\x0F
supybot.plugins.GitHub.format.release: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F $action \x0303$release__tag_name "|" $release__name\x0F - \x0313$release__html_url\x0F
supybot.plugins.GitHub.format.fork: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$forkee__owner__login\x0F forked the repository - \x0313$forkee__owner__html_url\x0F
supybot.plugins.GitHub.format.member: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F $action user \x0303$member__login\x0F - \x0313$member__html_url\x0F
supybot.plugins.GitHub.format.public: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F made the repository public!
supybot.plugins.GitHub.format.team_add: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" \x0307$sender__login\x0F added the team \x0303$team__name\x0F to the repository!
supybot.plugins.GitHub.format.status: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" [cif [ceq [echo $state] success] \"echo \x0303$state\x0F." \"echo \x0304$state\x0F.\"] $description - \x0313$target_url\x0F
supybot.plugins.GitHub.format.before.push: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" [cif [ceq [echo $pusher__name] none] \"echo \x0307A deploy key\x0F\" \"echo \x0307$pusher__name\x0F\"] pushed [echo $__num_commits] [cif [ceq [echo $__num_commits] 1] \"echo commit\" \"echo commits\"] to \x0303$ref__branch\x0F "[+$__files__added__len/-$__files__removed__len/\u00B1$__files__modified__len]" \x0313$compare\x0F
supybot.plugins.GitHub.format.push: echo "\x0F[\x0302$repository__owner__login/$repository__name\x0F]" [cif [ceq [echo $__commit__author__username] $__commit__author__username] "echo \x0307$__commit__author__name\x0F" "echo \x0307$__commit__author__username\x0F"] \x0303$__commit__id__short\x0F - $__commit__message__firstline
supybot.plugins.GitHub.format.push.hidden: echo (+$__hidden_commits hidden commits)
supybot.plugins.GitHub.format.workflow_run: echo "\x0f[\x0302$repository__owner__login/$repository__name\x0f]" Workflow Run for \x0307$workflow_run__name\x0f [cif [ceq [echo $workflow_run__conclusion] success] "echo \x0303$workflow_run__status\x0f" "cif [ceq [echo $workflow_run__conclusion] None] \\"echo $workflow_run__status\\" \\"echo \x0304$workflow_run__status\x0f\\""] on branch \x0303$workflow_run__head_branch\x0F. [cif [ceq [echo $workflow_run__conclusion] None] "echo \\"\\"" "echo $workflow_run__conclusion."] \x0313$workflow_run__html_url\x0f
```

If you use Continuous Integration external to GitHub (or if you like very noisy CI notifications from GitHub Workflows), use this instead of `check_run`:

```
supybot.plugins.GitHub.format.check_run: echo "\x0f[\x0302$repository__owner__login/$repository__name\x0f]" Check Run for \x0307$check_run__name\x0f [cif [ceq [echo $check_run__conclusion] success] "echo \x0303$check_run__status\x0f." "cif [ceq [echo $check_run__conclusion] None] \\"echo $check_run__status.\\" \\"echo \x0304$check_run__status\x0f.\\""] [cif [ceq [echo $check_run__conclusion] None] "echo \\"\\"" "echo $check_run__conclusion."] \x0313$check_run__details_url\x0f
```

To apply it, either use the Config plugin, or add them to your main `.conf` file.
