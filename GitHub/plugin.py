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

import sys
import json
import time
import urllib
import socket
import threading
import supybot.log as log
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.httpserver as httpserver

from . import ur1ca
if sys.version_info[0] < 3:
    from cStringIO import StringIO
else:
    from io import StringIO
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('GitHub')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

#####################
# Server stuff
#####################

class GithubCallback(httpserver.SupyHTTPServerCallback):
    name = "GitHub announce callback"
    defaultResponse = _("""
    You shouldn't be there, this subfolder is not for you. Go back to the
    index and try out other plugins (if any).""")
    def doPost(self, handler, path, form):
        if not handler.address_string().endswith('.rs.github.com') and \
                not handler.address_string().endswith('.cloud-ips.com') and \
                not handler.address_string() == 'localhost':
            log.warning("""'%s' tried to act as a web hook for Github,
            but is not GitHub.""" % handler.address_string())
            self.send_response(403)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('Error: you are not a GitHub server.')
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('Thanks.')
            self.plugin.announce.onPayload(json.loads(form['payload'].value))

#####################
# API access stuff
#####################

def query(caller, type_, uri_end, args):
    args = dict([(x,y) for x,y in args.items() if y is not None])
    url = '%s/%s/%s?%s' % (caller._url(), type_, uri_end,
                           urllib.urlencode(args))
    return json.load(utils.web.getUrlFd(url))

#####################
# Plugin itself
#####################

instance = None

@internationalizeDocstring
class GitHub(callbacks.Plugin):
    """Add the help for "@plugin help GitHub" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        global instance
        self.__parent = super(GitHub, self)
        callbacks.Plugin.__init__(self, irc)
        instance = self

        callback = GithubCallback()
        callback.plugin = self
        httpserver.hook('github', callback)

    class announce(callbacks.Commands):
        def _createPrivmsg(self, channel, payload, commit, hidden=None):
            bold = ircutils.bold
            url = commit['url']

            # ur1.ca
            try:
                post_param = ur1ca.parameterize(url)
                answerfile = ur1ca.request(post_param)
                doc = ur1ca.retrievedoc(answerfile)
                answerfile.close()
                status, url2 = ur1ca.scrape(doc)

                if status:
                    url = url2
            except Exception as e:
                log.error('Cannot connect to ur1.ca: %s' % e)

            s = _('%s/%s (in %s): %s committed %s %s') % \
                    (payload['repository']['owner']['name'],
                     bold(payload['repository']['name']),
                     bold(payload['ref'].split('/')[-1]),
                     commit['author']['name'],
                     bold(commit['message'].split('\n')[0]),
                     url)
            if hidden is not None:
                s += _(' (+ %i hidden commits)') % hidden
            return ircmsgs.privmsg(channel, s.encode('utf8'))

        def onPayload(self, payload):
            repo = '%s/%s' % (payload['repository']['owner']['name'],
                              payload['repository']['name'])
            announces = self._load()
            if repo not in announces:
                log.info('Commit for repo %s not announced anywhere' % repo)
                return
            for channel in announces[repo]:
                for irc in world.ircs:
                    if channel in irc.state.channels:
                        break
                commits = payload['commits']
                if channel not in irc.state.channels:
                    log.info('Cannot announce commit for repo %s on %s' %
                             (repo, channel))
                elif len(commits) == 0:
                    log.warning('GitHub callback called without any commit.')
                else:
                    hidden = None
                    last_commit = commits[-1]
                    if last_commit['message'].startswith('Merge ') and \
                            len(commits) > 5:
                        hidden = len(commits) + 1
                        payload['commits'] = [last_commit]
                    for commit in payload['commits']:
                        msg = self._createPrivmsg(channel, payload, commit,
                                hidden)
                        irc.queueMsg(msg)

        def _load(self):
            announces = instance.registryValue('announces').split(' || ')
            if announces == ['']:
                return {}
            announces = [x.split(' | ') for x in announces]
            output = {}
            for repo, chan in announces:
                if repo not in output:
                    output[repo] = []
                output[repo].append(chan)
            return output

        def _save(self, data):
            list_ = []
            for repo, chans in data.items():
                list_.extend([' | '.join([repo,chan]) for chan in chans])
            string = ' || '.join(list_)
            instance.setRegistryValue('announces', value=string)

        @internationalizeDocstring
        def add(self, irc, msg, args, channel, owner, name):
            """[<channel>] <owner> <name>

            Announce the commits of the GitHub repository called
            <owner>/<name> in the <channel>.
            <channel> defaults to the current channel."""
            repo = '%s/%s' % (owner, name)
            announces = self._load()
            if repo not in announces:
                announces[repo] = [channel]
            elif channel in announces[repo]:
                irc.error(_('This repository is already announced to this '
                            'channel.'))
                return
            else:
                announces[repo].append(channel)
            self._save(announces)
            irc.replySuccess()
        add = wrap(add, ['channel', 'something', 'something'])

        @internationalizeDocstring
        def remove(self, irc, msg, args, channel, owner, name):
            """[<channel>] <owner> <name>

            Don't announce the commits of the GitHub repository called
            <owner>/<name> in the <channel> anymore.
            <channel> defaults to the current channel."""
            repo = '%s/%s' % (owner, name)
            announces = self._load()
            if repo not in announces:
                announces[repo] = []
            elif channel not in announces[repo]:
                irc.error(_('This repository is not yet announced to this '
                            'channel.'))
                return
            else:
                announces[repo].remove(channel)
            self._save(announces)
            irc.replySuccess()
        remove = wrap(remove, ['channel', 'something', 'something'])



    class repo(callbacks.Commands):
        def _url(self):
            url = instance.registryValue('api.url')
            if url == 'http://github.com/api/v2/json': # old api
                url = 'https://api.github.com'
                instance.setRegistryValue('api.url', value=url)
            return url

        @internationalizeDocstring
        def search(self, irc, msg, args, search, optlist):
            """<searched string> [--page <id>] [--language <language>]

            Searches the string in the repository names database. You can
            specify the page <id> of the results, and restrict the search
            to a particular programming <language>."""
            args = {'page': None, 'language': None}
            for name, value in optlist:
                if name in args:
                    args[name] = value
            results = query(self, 'legacy/repos/search',
                    urllib.quote_plus(search), args)
            reply = ' & '.join('%s/%s' % (x['owner'], x['name'])
                               for x in results['repositories'])
            if reply == '':
                irc.error(_('No repositories matches your search.'))
            else:
                irc.reply(reply.encode('utf8'))
        search = wrap(search, ['something',
                               getopts({'page': 'id',
                                        'language': 'somethingWithoutSpaces'})])
        @internationalizeDocstring
        def info(self, irc, msg, args, owner, name, optlist):
            """<owner> <repository> [--enable <feature> <feature> ...] \
            [--disable <feature> <feature>]

            Displays informations about <owner>'s <repository>.
            Enable or disable features (ie. displayed data) according to the
            request)."""
            enabled = ['watchers', 'forks', 'pushed_at', 'open_issues',
                       'description']
            for mode, features in optlist:
                features = features.split(' ')
                for feature in features:
                    if mode == 'enable':
                        enabled.append(feature)
                    else:
                        try:
                            enabled.remove(feature)
                        except ValueError:
                            # No error is raised, because:
                            # 1. it wouldn't break anything
                            # 2. it enhances cross-compatiblity
                            pass
            results = query(self, 'repos', '%s/%s' % (owner, name), {})
            output = []
            for key, value in results.items():
                if key in enabled:
                    output.append('%s: %s' % (key, value))
            irc.reply(', '.join(output).encode('utf8'))
        info = wrap(info, ['something', 'something',
                           getopts({'enable': 'anything',
                                    'disable': 'anything'})])
    def die(self):
        self.__parent.die()
        httpserver.unhook('github')


Class = GitHub


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
