###
# Copyright (c) 2012, Valentin Lorentz
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
import requests

import supybot.utils as utils
import supybot.schedule as schedule
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('TwitterStream')

@internationalizeDocstring
class TwitterStream(callbacks.Plugin):
    """Add the help for "@plugin help TwitterStream" here
    This should describe *how* to use this plugin."""
    threaded = True

    _users = {}
    _searches = {}

    def user(self, irc, msg, arg, username):
        """<username>

        Start usering a Twitter account."""
        name = 'twitterstream_user_'+username
        api = twitter.Api()
        def fetch(send=True):
            timeline = api.GetUserTimeline(username,
                    since_id=self._users[name])
            for tweet in timeline:
                self._users[name] = max(self._users[name], tweet.id)
            format_ = '@%(user)s> %(msg)s'
            replies = [format_ % {'longid': x.id,
                                  'user': x.user.screen_name,
                                  'msg': x.text
                                 } for x in timeline]
            replies = [x.replace("&lt;", "<").replace("&gt;", ">")
                    .replace("&amp;", "&") for x in replies]
            if send:
                for reply in replies:
                    irc.reply(reply, prefixNick=False)
        self._users[name] = 0
        fetch(False)
        schedule.addPeriodicEvent(fetch, 60, name)
        irc.replySuccess()
    user = wrap(user, ['text'])

    def search(self, irc, msg, arg, search):
        """<terms>

        Start streaming a Twitter search."""
        name = 'twitterstream_search_'+search
        api = twitter.Api()
        def fetch(send=True):
            url = 'http://search.twitter.com/search.json?q=%s&since_id=%i' % \
                    (search, self._searches[name])
            timeline = requests.get(url).json['results']
            for tweet in timeline:
                self._searches[name] = max(self._searches[name], tweet['id'])
            format_ = '@%(user)s> %(msg)s'
            replies = [format_ % {'longid': x['id'],
                                  'user': x['from_user'],
                                  'msg': x['text']
                                 } for x in timeline
                                 if not x['text'].startswith('RT ')]
            replies = [x.replace("&lt;", "<").replace("&gt;", ">")
                    .replace("&amp;", "&") for x in replies]
            if send:
                for reply in replies:
                    irc.reply(reply, prefixNick=False)
        self._searches[name] = 0
        fetch(False)
        schedule.addPeriodicEvent(fetch, 60, name)
        irc.replySuccess()
    search = wrap(search, ['text'])

    def die(self):
        for user in self._users:
            schedule.removeEvent(user)
        for search in self._searches:
            schedule.removeEvent(search)
        self._streams = []
        self._searches = []


Class = TwitterStream


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
