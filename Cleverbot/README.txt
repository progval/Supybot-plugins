Cleverbot Plugin for Supybots
==============================
Author: Albert Huang (alberthrocks)

This is a plugin that uses the Cleverbot AI bot service to generate somewhat
coherent AI responses to humans. As indicated, it is designed to be loaded
into Supybot.

The plugin responds by using an invalid command callback/hook to get the
question and send back the response.

This is only a proof of concept - under no circumstances should it be used in
a production environment. Cleverbot may ban you for using their service this
way, so beware.

This plugin was forked from a similar project, supybot-pandorabots, which uses
the Pandorabots AI API to generate responses. You can find that project here:
https://launchpad.net/supybot-pandorabots 

By using this software, you comply to the GPL v3, especially the NO WARRANTY
part. See LICENSE.txt for more information. I do not provide support - you
should not expect any fixes made. (Maybe I'll fix code under rare
circumstances... and maybe if there's demand!)

To install, just copy this folder into your supybot plugins folder and load it.
Note that if you are running any existing AIs, like Pandorabots, you need to
disable them before using this AI.

If you find any bugs, or have just something to say, feel free to join
#talkingbots on EFNet or Freenode, file a bug report, or email me!

This plugin uses PyCleverbot (the reason this was all possible), which can be
found here:
http://code.google.com/p/pycleverbot/
