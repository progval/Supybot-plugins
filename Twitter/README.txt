Advanced Twitter plugin for Supybot, with capabilities handling, and
per-channel user account.

Configuration
=============

Ever noticed a text "sent from web" or "sent via Android" under a tweet?
This is called the consumer. You have two choices:
* Keep the default consumer. This is the easier way; and the text will
  be "sent via Supybot // Limnoria".
* Create your own consumer at https://dev.twitter.com/ . If you choosed
  this way, you will have to set supybot.plugins.Twitter.consumer.key
  and supybot.plugins.Twitter.consumer.secret with the consumer
  key/secret given by Twitter.


Now, you have to set the accounts credentials (called access token)
for every channel you want to associate with a Twitter account.

If you use the default consumer, it is easy : just run the get_access_token.py
script provided with this plugin.
Otherwise, you will have either to edit the script with your own consumer
key/secret and run it, or get the token from dev.twitter.com.



Once you got the token key/secret, set it _as a channel-specific variable_
to supybot.plugins.Twitter.accounts.channel.key and 
supybot.plugins.Twitter.accounts.channel.secret.


Capabilities
============

All users are allowed to use all commands by default! Use this command to
disable account administration (follow, unfollow, ...) by default:
@defaultcapability add -twitteradmin

To disable posts and retweets by default, use this one:
@defaultcapability add -twitterpost

Extra features
==============

If the Untiny plugin is loaded, this plugin will automaticaly extract original
links from t.co ones.
