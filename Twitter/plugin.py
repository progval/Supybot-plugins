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

import twitter
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Twitter')

reload(twitter)
if twitter.__version__.split('.') < ['0', '8', '0']:
    raise ImportError('You current version of python-twitter is to old, '
                      'you need at least version 0.8.0, because older '
                      'versions do not support OAuth authentication.')

@internationalizeDocstring
class Twitter(callbacks.Plugin):
    """Add the help for "@plugin help Twitter" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Twitter, self)
        callbacks.Plugin.__init__(self, irc)
        self._apis = {}

    def _getApi(self, channel):
        if channel in self._apis:
            return self._apis[channel]
        if channel is None:
            key = self.registryValue('accounts.bot.key')
            secret = self.registryValue('accounts.bot.secret')
        else:
            key = self.registryValue('accounts.channel.key', channel)
            secret = self.registryValue('accounts.channel.secret', channel)
        if key == '' or secret == '':
            return twitter.Api()
        api = twitter.Api(consumer_key='bItq1HZhBGyx5Y8ardIeQ',
                consumer_secret='qjC6Ye6xSMM3XPLR3LLeMqOP4ri0rgoYFT2si1RpY',
                access_token_key=key,
                access_token_secret=secret)
        self._apis[channel] = api
        return api


    @internationalizeDocstring
    def friendslist(self, irc, msg, args, channel, user):
        """[<channel>] [<user>]

        Replies with the friends (i.e. people who one subscribes to) of the
        <user>, as the <channel> associated account. <channel> is only
        needed if you don't run the command in the channel itself. If <user>
        is not given, it defaults to the channel's account."""
        api = self._getApi(channel)
        if not api._oauth_consumer and user is None:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel, or provide '
                        'a user name.'))
            return
        friends = api.GetFriends(user) # If user is not given, it defaults
                                       # to None, and giving None to
                                       # GetFriends() has the expected
                                       # behaviour.
        reply = utils.str.format("%L", ['%s(%s)' % (x.name, x.screen_name)
                                        for x in friends])
        reply = reply.encode('utf8')
        irc.reply(reply)
    friendslist = wrap(friendslist, ['channel',
                                     optional('somethingWithoutSpaces')])

    @internationalizeDocstring
    def post(self, irc, msg, args, user, channel, message):
        """[<channel>] <message>

        Updates the status of the account associated with the given <channel>
        to the <message>. If <channel> is not given, it defaults to the
        current channel."""
        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel.'))
            return
        api.PostUpdate('[%s] %s' % (user.name, message))
        irc.replySuccess()
    post = wrap(post, ['user', ('checkChannelCapability', 'twitter'), 'text'])



    def die(self):
        self.__parent.die()

Class = Twitter


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
