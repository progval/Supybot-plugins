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

from __future__ import division


import re
import sys
import time
import json
import operator
import functools
import threading
import supybot.log as log
import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.registry as registry
import supybot.callbacks as callbacks
if sys.version_info[0] < 3:
    import htmlentitydefs
else:
    import html.entities as htmlentitydefs
    from imp import reload
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Twitter')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

try:
    import twitter
except ImportError:
    raise callbacks.Error('You need the python-twitter library.')
reload(twitter)
if not hasattr(twitter, '__version__') or \
        twitter.__version__.split('.') < ['0', '8', '0']:
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
        data = self._FetchUrl(url, post_data={'dummy': None})
        data = json.loads(data)
        self._CheckForTwitterError(data)
        return twitter.Status.NewFromJsonDict(data)

_tco_link_re = re.compile('http://t.co/[a-zA-Z0-9]+')
def expandLinks(tweet):
    if 'Untiny.plugin' in sys.modules:
        def repl(link):
            return sys.modules['Untiny.plugin'].Untiny(None) \
                    ._untiny(None, link.group(0))
        return _tco_link_re.sub(repl, tweet)
    else:
        return tweet

def fetch(method, maxIds, name):
    if name not in maxIds:
        maxIds[name] = None
    if maxIds[name] is None:
        tweets = method()
    else:
        tweets = method(since_id=maxIds[name])
    if not tweets:
        return []

    if maxIds[name] is None:
        maxIds[name] = tweets[-1].id
        return []
    else:
        maxIds[name] = tweets[-1].id
        return tweets


@internationalizeDocstring
class Twitter(callbacks.Plugin):
    """Add the help for "@plugin help Twitter" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Twitter, self)
        callbacks.Plugin.__init__(self, irc)
        self._apis = {}
        self._died = False
        if world.starting:
            try:
                self._getApi().PostUpdate(_('I just woke up. :)'))
            except:
                pass
        self._runningAnnounces = []
        try:
            conf.supybot.plugins.Twitter.consumer.key.addCallback(
                    self._dropApiObjects)
            conf.supybot.plugins.Twitter.consumer.secret.addCallback(
                    self._dropApiObjects)
            conf.supybot.plugins.Twitter.accounts.channel.key.addCallback(
                    self._dropApiObjects)
            conf.supybot.plugins.Twitter.accounts.channel.secret.addCallback(
                    self._dropApiObjects)
            conf.supybot.plugins.Twitter.accounts.channel.api.addCallback(
                    self._dropApiObjects)
        except registry.NonExistentRegistryEntry:
            log.error('Your version of Supybot is not compatible with '
                      'configuration hooks. So, Twitter won\'t be able '
                      'to apply changes to the consumer key/secret '
                      'and token key/secret unless you reload it.')
        self._shortids = {}
        self._current_shortid = 0

    def _dropApiObjects(self, name=None):
        self._apis = {}


    def _getApi(self, channel):
        if channel in self._apis:
            # TODO: handle configuration changes (using Limnoria's config hooks)
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
            return ExtendedApi(base_url=url)
        api = ExtendedApi(consumer_key=self.registryValue('consumer.key'),
                consumer_secret=self.registryValue('consumer.secret'),
                access_token_key=key,
                access_token_secret=secret,
                base_url=url)
        self._apis[channel] = api
        return api

    def _get_shortid(self, longid):
        characters = '0123456789abcdefghijklmnopwrstuvwyz'
        id_ = self._current_shortid + 1
        id_ %= (36**4)
        self._current_shortid = id_
        shortid = ''
        while len(shortid) < 3:
            quotient, remainder = divmod(id_, 36)
            shortid = characters[remainder] + shortid
            id_ = quotient
        self._shortids[shortid] = longid
        return shortid

    def _unescape(self, text):
        """Created by Fredrik Lundh (http://effbot.org/zone/re-sub.htm#unescape-html)"""
        text = text.replace("\n", " ")
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except (ValueError, OverflowError):
                    pass
            else:
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text # leave as is
        return re.sub("&#?\w+;", fixup, text)

    def __call__(self, irc, msg):
        super(Twitter, self).__call__(irc, msg)
        irc = callbacks.SimpleProxy(irc, msg)
        for channel in irc.state.channels:
            if self.registryValue('announce.interval', channel) != 0 and \
                    channel not in self._runningAnnounces:
                threading.Thread(target=self._fetchTimeline,
                        args=(irc, channel),
                        name='Twitter timeline for %s' % channel).start()

    def _fetchTimeline(self, irc, channel):
        if channel in self._runningAnnounces:
            # Prevent race conditions
            return
        lastRun = time.time()
        maxIds = {}
        self._runningAnnounces.append(channel)
        try:
            while not irc.zombie and not self._died and \
                    self.registryValue('announce.interval', channel) != 0:
                while lastRun is not None and \
                        lastRun+self.registryValue('announce.interval', channel)>time.time():
                    time.sleep(5)
                lastRun = time.time()
                self.log.debug(_('Fetching tweets for channel %s') % channel)
                api = self._getApi(channel) # Reload it from conf everytime
                if not api._oauth_consumer:
                    return
                retweets = self.registryValue('announce.retweets', channel)
                try:
                    tweets = []
                    if self.registryValue('announce.timeline', channel):
                        tweets.extend(fetch(
                            functools.partial(api.GetFriendsTimeline,
                                              retweets=retweets),
                            maxIds, 'timeline'))
                    if self.registryValue('announce.mentions', channel):
                        tweets.extend(fetch(api.GetReplies,
                            maxIds, 'mentions'))
                    for user in self.registryValue('announce.users', channel):
                        if not user.startswith('@'):
                            user = '@' + user
                        tweets.extend(fetch(
                            functools.partial(api.GetUserTimeline,
                                screen_name=user[1:]),
                            maxIds, user))
                except twitter.TwitterError as e:
                    self.log.error('Could not fetch timeline: %s' % e)
                    continue
                if not tweets:
                    continue
                tweets.sort(key=operator.attrgetter('id'))
                format_ = '@%(user)s> %(msg)s'
                if self.registryValue('announce.withid', channel):
                    format_ = '[%(longid)s] ' + format_
                if self.registryValue('announce.withshortid', channel):
                    format_ = '(%(shortid)s) ' + format_
                replies = [format_ % {'longid': x.id,
                                      'shortid': self._get_shortid(x.id),
                                      'user': x.user.screen_name,
                                      'msg': x.text
                                     } for x in tweets]

                replies = map(self._unescape, replies)
                replies = map(expandLinks, replies)
                if self.registryValue('announce.oneline', channel):
                    irc.replies(replies, prefixNick=False, joiner=' | ',
                            to=channel)
                else:
                    for reply in replies:
                        irc.reply(reply, prefixNick=False, to=channel)
        finally:
            assert channel in self._runningAnnounces
            self._runningAnnounces.remove(channel)



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
        reply = self._unescape(reply)
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
        reply = self._unescape(reply)
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
        if self.registryValue('prefixusername', channel):
            tweet = '[%s] %s' % (user.name, tweet)
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
            if len(id_) <= 3:
                try:
                    id_ = self._shortids[id_]
                except KeyError:
                    irc.error(_('This is not a valid ID.'))
                    return
            else:
                try:
                    id_ = int(id_)
                except ValueError:
                    irc.error(_('This is not a valid ID.'))
                    return
            api.PostRetweet(id_)
            irc.replySuccess()
        except twitter.TwitterError as e:
            irc.error(e.args[0])
    retweet = wrap(retweet, ['user', ('checkChannelCapability', 'twitterpost'),
            'somethingWithoutSpaces'])

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
            timeline = api.GetUserTimeline(screen_name=user,
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
            reply = ' | '.join(['[%s] %s' % (x.id, expandLinks(x.text))
                    for x in timeline])
        else:
            reply = ' | '.join([expandLinks(x.text) for x in timeline])

        reply = self._unescape(reply)
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
        reply = ' | '.join([expandLinks(x.text) for x in public])

        reply = self._unescape(reply)
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
        id_ = optlist['since'] or '0000'

        if len(id_) <= 3:
            try:
                id_ = self._shortids[id_]
            except KeyError:
                irc.error(_('This is not a valid ID.'))
                return
        else:
            try:
                id_ = int(id_)
            except ValueError:
                irc.error(_('This is not a valid ID.'))
                return

        api = self._getApi(channel)
        try:
            replies = api.GetReplies(since_id=id_)
        except twitter.TwitterError:
            irc.error(_('No tweets'))
            return
        reply = ' | '.join(["%s: %s" % (x.user.screen_name, expandLinks(x.text))
                for x in replies])

        reply = self._unescape(reply)
        irc.reply(reply)
    replies = wrap(replies, ['channel',
        getopts({'since': 'somethingWithoutSpaces'})])

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
        reply = self._unescape(reply)
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
    def delete(self, irc, msg, args, channel, id_):
        """[<channel>] <id>

        Delete a specified status with id <id>
        If <channel> is not given, it defaults to the current channel.
        """
        if len(id_) <= 3:
            try:
                id_ = self._shortids[id_]
            except KeyError:
                irc.error(_('This is not a valid ID.'))
                return
        else:
            try:
                id_ = int(id_)
            except ValueError:
                irc.error(_('This is not a valid ID.'))
                return

        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel.'))
            return
        try:
            delete = api.DestroyStatus(id_)
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
    def profile(self, irc, msg, args, channel, user=None):
        """[<channel>] [<user>]

        Return profile image for a specified <user>
        If <channel> is not given, it defaults to the current channel.
        """

        api = self._getApi(channel)
        if not api._oauth_consumer:
            irc.error(_('No account is associated with this channel. Ask '
                        'an op, try with another channel.'))
            return
        try:
            if user:
                profile = api.GetUser(user)
            else:
                profile = api.VerifyCredentials()
        except twitter.TwitterError:
            irc.error(_('An error occurred'))
            return

        irc.reply(('Name: @%s (%s). Profile picture: %s. Biography: %s') %
                (profile.screen_name,
                 profile.name,
                 profile.GetProfileImageUrl().replace('_normal', ''),
                 profile.description))
    profile = wrap(profile, ['channel', optional('somethingWithoutSpaces')])


    def die(self):
        self.__parent.die()
        self._died = True

Class = Twitter


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

