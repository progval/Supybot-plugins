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
import simplejson
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Twitter')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

reload(twitter)
if twitter.__version__.split('.') < ['0', '8', '0']:
    raise ImportError('You current version of python-twitter is to old, '
                      'you need at least version 0.8.0, because older '
                      'versions do not support OAuth authentication.')

class ExtendedApi(twitter.Api):
    """Api with retweet support."""

    def PostRetweet(self, id):
        '''Retweet a tweet with the Retweet API

        The twitter.Api instance must be authenticated.

        Args:
        id: The numerical ID of the tweet you are retweeting

        Returns:
        A twitter.Status instance representing the retweet posted
        '''
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        try:
            if int(id) <= 0:
                raise TwitterError("'id' must be a positive number")
        except ValueError:
            raise TwitterError("'id' must be an integer")
        url = 'http://api.twitter.com/1/statuses/retweet/%s.json' % id
        json = self._FetchUrl(url, post_data={'dummy': None})
        data = simplejson.loads(json)
        self._CheckForTwitterError(data)
        return twitter.Status.NewFromJsonDict(data)



@internationalizeDocstring
class Twitter(callbacks.Plugin):
    """Add the help for "@plugin help Twitter" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Twitter, self)
        callbacks.Plugin.__init__(self, irc)
        self._apis = {}
        if world.starting:
            try:
                self._getApi().PostUpdate(_('I just woke up. :)'))
            except:
                pass

    def _getApi(self, channel):
        if channel in self._apis:
            return self._apis[channel]
        if channel is None:
            key = self.registryValue('accounts.bot.key')
            secret = self.registryValue('accounts.bot.secret')
            url = self.registryValue('accounts.bot.api')
        else:
            key = self.registryValue('accounts.channel.key', channel)
            secret = self.registryValue('accounts.channel.secret', channel)
            url = self.registryValue('accounts.channel.api')
        if key == '' or secret == '':
            return twitter.Api(base_url=url)
        api = ExtendedApi(consumer_key='bItq1HZhBGyx5Y8ardIeQ',
                consumer_secret='qjC6Ye6xSMM3XPLR3LLeMqOP4ri0rgoYFT2si1RpY',
                access_token_key=key,
                access_token_secret=secret,
                base_url=url)
        self._apis[channel] = api
        return api


    @internationalizeDocstring
    def following(self, irc, msg, args, channel, user):
        """[<channel>] [<user>]

        Replies with the people this <user> follows. If <user> is not given, it
        defaults to the <channel>'s account. If <channel> is not given, it
        defaults to the current channel."""
        api = self._getApi(channel)
        if not api._oauth_consumer and user is None:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel, or provide '
                        'a user name.'))
            return
        following = api.GetFriends(user) # If user is not given, it defaults
                                       # to None, and giving None to
                                       # GetFriends() has the expected
                                       # behaviour.
        reply = utils.str.format("%L", ['%s (%s)' % (x.name, x.screen_name)
                                        for x in following])
        reply = reply.encode('utf8')
        irc.reply(reply)
    following = wrap(following, ['channel',
                                     optional('somethingWithoutSpaces')])

    @internationalizeDocstring
    def followers(self, irc, msg, args, channel):
        """[<channel>]

        Replies with the people that follow this account. If <channel> is not
        given, it defaults to the current channel."""
        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel, or provide '
                        'a user name.'))
            return
        followers = api.GetFollowers()
        reply = utils.str.format("%L", ['%s (%s)' % (x.name, x.screen_name)
                                        for x in followers])
        reply = reply.encode('utf8')
        irc.reply(reply)
    followers = wrap(followers, ['channel'])

    @internationalizeDocstring
    def dm(self, irc, msg, args, user, channel, recipient, message):
        """[<channel>] <recipient> <message>

        Sends a <message> to <recipient> from the account associated with the
        given <channel>. If <channel> is not given, it defaults to the current
        channel."""
        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op or try with another channel.'))
            return

        if len(message) > 140:
            irc.error(_('Sorry, your message exceeds 140 characters (%i)') %
                    len(message))
        else:
            api.PostDirectMessage(recipient, message)
            irc.replySuccess()
    dm = wrap(dm, ['user', ('checkChannelCapability', 'twitteradmin'),
                   'somethingWithoutSpaces', 'text'])

    @internationalizeDocstring
    def post(self, irc, msg, args, user, channel, message):
        """[<channel>] <message>

        Updates the status of the account associated with the given <channel>
        to the <message>. If <channel> is not given, it defaults to the
        current channel."""
        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op or try with another channel.'))
            return
        tweet = message
        if len(tweet) > 140:
            irc.error(_('Sorry, your tweet exceeds 140 characters (%i)') %
                    len(tweet))
        else:
            api.PostUpdate(tweet)
            irc.replySuccess()
    post = wrap(post, ['user', ('checkChannelCapability', 'twitterpost'), 'text'])

    @internationalizeDocstring
    def retweet(self, irc, msg, args, user, channel, id_):
        """[<channel>] <id>

        Retweets the message with the given ID."""
        api = self._getApi(channel)
        try:
            api.PostRetweet(id_)
            irc.replySuccess()
        except twitter.TwitterError as e:
            irc.error(e.args[0])
    retweet = wrap(retweet, ['user', ('checkChannelCapability', 'twitterpost'),
            'int'])

    @internationalizeDocstring
    def timeline(self, irc, msg, args, channel, tupleOptlist, user):
        """[<channel>] [--since <oldest>] [--max <newest>] [--count <number>] \
        [--noretweet] [--with-id] [<user>]

        Replies with the timeline of the <user>.
        If <user> is not given, it defaults to the account associated with the
        <channel>.
        If <channel> is not given, it defaults to the current channel.
        If given, --since and --max take tweet IDs, used as boundaries.
        If given, --count takes an integer, that stands for the number of
        tweets to display.
        If --noretweet is given, only native user's tweet will be displayed.
        """
        optlist = {}
        for key, value in tupleOptlist:
            optlist.update({key: value})
        for key in ('since', 'max', 'count'):
            if key not in optlist:
                optlist[key] = None
        optlist['noretweet'] = 'noretweet' in optlist
        optlist['with-id'] = 'with-id' in optlist

        api = self._getApi(channel)
        if not api._oauth_consumer and user is None:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel.'))
            return
        try:
            timeline = api.GetUserTimeline(id=user,
                                           since_id=optlist['since'],
                                           max_id=optlist['max'],
                                           count=optlist['count'],
                                           include_rts=not optlist['noretweet'])
        except twitter.TwitterError:
            irc.error(_('This user protects his tweets; you need to fetch '
                        'them from a channel whose associated account can '
                        'fetch this timeline.'))
            return
        if optlist['with-id']:
            reply = ' | '.join(['[%s] %s' % (x.id, x.text) for x in timeline])
        else:
            reply = ' | '.join([x.text for x in timeline])

        reply = reply.replace("&lt;", "<")
        reply = reply.replace("&gt;", ">")
        reply = reply.replace("&amp;", "&")
        reply = reply.encode('utf8')
        irc.reply(reply)
    timeline = wrap(timeline, ['channel',
                               getopts({'since': 'int',
                                        'max': 'int',
                                        'count': 'int',
                                        'noretweet': '',
                                        'with-id': ''}),
                               optional('somethingWithoutSpaces')])

    @internationalizeDocstring
    def public(self, irc, msg, args, channel, tupleOptlist):
        """[<channel>] [--since <oldest>]

        Replies with the public timeline.
        If <channel> is not given, it defaults to the current channel.
        If given, --since takes a tweet ID, used as a boundary
        """
        optlist = {}
        for key, value in tupleOptlist:
            optlist.update({key: value})

        if 'since' not in optlist:
            optlist['since'] = None

        api = self._getApi(channel)
        try:
            public = api.GetPublicTimeline(since_id=optlist['since'])
        except twitter.TwitterError:
            irc.error(_('No tweets'))
            return
        reply = ' | '.join([x.text for x in public])

        reply = reply.replace("&lt;", "<")
        reply = reply.replace("&gt;", ">")
        reply = reply.replace("&amp;", "&")
        reply = reply.encode('utf8')
        irc.reply(reply)
    public = wrap(public, ['channel', getopts({'since': 'int'})])

    @internationalizeDocstring
    def replies(self, irc, msg, args, channel, tupleOptlist):
        """[<channel>] [--since <oldest>]

        Replies with the replies timeline.
        If <channel> is not given, it defaults to the current channel.
        If given, --since takes a tweet ID, used as a boundary
        """
        optlist = {}
        for key, value in tupleOptlist:
            optlist.update({key: value})

        if 'since' not in optlist:
            optlist['since'] = None

        api = self._getApi(channel)
        try:
            replies = api.GetReplies(since_id=optlist['since'])
        except twitter.TwitterError:
            irc.error(_('No tweets'))
            return
        reply = ' | '.join(["%s: %s" % (x.user.screen_name, x.text) for x in replies])

        reply = reply.replace("&lt;", "<")
        reply = reply.replace("&gt;", ">")
        reply = reply.replace("&amp;", "&")
        reply = reply.encode('utf8')
        irc.reply(reply)
    replies = wrap(replies, ['channel', getopts({'since': 'int'})])

    @internationalizeDocstring
    def trends(self, irc, msg, args, channel):
        """[<channel>]

        Current trending topics
        If <channel> is not given, it defaults to the current channel.
        """

        api = self._getApi(channel)
        try:
            trends = api.GetTrendsCurrent()
        except twitter.TwitterError:
            irc.error(_('No tweets'))
            return
        reply = ' | '.join([x.name for x in trends])
        reply = reply.encode('utf8')
        irc.reply(reply)
    trends = wrap(trends, ['channel'])

    @internationalizeDocstring
    def follow(self, irc, msg, args, channel, user):
        """[<channel>] <user>

        Follow a specified <user>
        If <channel> is not given, it defaults to the current channel.
        """

        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel.'))
            return
        try:
            follow = api.CreateFriendship(user)
        except twitter.TwitterError:
            irc.error(_('An error occurred'))
            return

        irc.replySuccess()
    follow = wrap(follow, ['channel', ('checkChannelCapability', 'twitteradmin'),
                           'somethingWithoutSpaces'])

    @internationalizeDocstring
    def unfollow(self, irc, msg, args, channel, user):
        """[<channel>] <user>

        Unfollow a specified <user>
        If <channel> is not given, it defaults to the current channel.
        """

        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel.'))
            return
        try:
            unfollow = api.DestroyFriendship(user)
        except twitter.TwitterError:
            irc.error(_('An error occurred'))
            return

        irc.replySuccess()
    unfollow = wrap(unfollow, ['channel',
                               ('checkChannelCapability', 'twitteradmin'),
                               'somethingWithoutSpaces'])

    @internationalizeDocstring
    def delete(self, irc, msg, args, channel, id):
        """[<channel>] <id>

        Delete a specified status with id <id>
        If <channel> is not given, it defaults to the current channel.
        """

        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel.'))
            return
        try:
            delete = api.DestroyStatus(id)
        except twitter.TwitterError:
            irc.error(_('An error occurred'))
            return

        irc.replySuccess()
    delete = wrap(delete, ['channel',
                               ('checkChannelCapability', 'twitteradmin'),
                               'somethingWithoutSpaces'])

    @internationalizeDocstring
    def stats(self, irc, msg, args, channel):
        """[<channel>]

        Print some stats
        If <channel> is not given, it defaults to the current channel.
        """
        api = self._getApi(channel)
        try:
            reply = {}
            reply['followers'] = len(api.GetFollowers())
            reply['following'] = len(api.GetFriends(None))
        except twitter.TwitterError:
            irc.error(_('An error occurred'))
            return
        reply = "I am following %d people and have %d followers" % (reply['following'], reply['followers'])
        irc.reply(reply)
    stats = wrap(stats, ['channel'])

    @internationalizeDocstring
    def profile(self, irc, msg, args, channel, user):
        """[<channel>] <user>

        Return profile image for a specified <user>
        If <channel> is not given, it defaults to the current channel.
        """

        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel.'))
            return
        try:
            profile = api.GetUser(user)
        except twitter.TwitterError:
            irc.error(_('An error occurred'))
            return

        irc.reply(profile.GetProfileImageUrl().replace('_normal', ''))
    profile = wrap(profile, ['channel', 'somethingWithoutSpaces'])


    def die(self):
        self.__parent.die()

Class = Twitter


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
