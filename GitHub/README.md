This plugin announces events GitHub repositories to IRC.

**This plugin requires Limnoria.**

To use this plugin you must forward/open the port which is specified by 
the configuration variable `supybot.servers.http.port` (8080 is the 
default value).

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
