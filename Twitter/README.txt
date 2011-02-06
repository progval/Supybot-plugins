SupyBot Twitter Plugin
======================

This plugin uses the Twitter API from http://code.google.com/p/python-twitter/

It must be installed and available for use.

To use:
  !twitter <msg>
    Sends <msg> to the twitter network.
    If <msg> is one of the twitter commands, it is sent raw, via the
    	associated twitter user.
    If not, the IRC user's name is appended to <msg> and is then sent.

  Incoming twitter notifications are automatically echoed to the channel
