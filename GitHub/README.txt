This plugin announces pushes and (commits) to GitHub repositories to IRC.

To use this plugin you must forward/open the port which is specified by the configuration variable
"supybot.servers.http.port" (8080 is the default value).

To add announces use the command "github announce add <owner> <repo>" Owner means owner of the repository (GitHub username.)
and repo what git repository the bot should announce. When you want to remove announce, use the command "github announce remove <owner> <repo>".

Please note that the names are case-sensitive. If you use mis-spelled repository names, the bot will not announce commits to that repository.

To get the bot notified about commits, you must tell GitHub to post to your bot. (GitHub explanation: http://help.github.com/post-receive-hooks/ )
In order to do that, you must go admin page of repo, tab service hooks (direct link: https://github.com/<owner>/<repo>/admin/hooks ) and select "Post-Receive URLs". Choose it
and add URL of your bot there. The URL is http://<IP or dynamicdns-service>:<port>/github .

Now your bot should announce all commits. To test this go back to "Post-Reveive URLs" and press "Test Hook".
This causes your bot to announce the last three commits. If the bot doesn't see them, check what you ordered it to announce and is that correct URL correct in "Post-Receive URLs" and is the port opened/forwarded.
