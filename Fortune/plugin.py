###
# Copyright (c) 2014, Valentin Lorentz
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
import random
import itertools

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.registry as registry
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Fortune')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

if sys.version_info[0] >= 3:
    (imap, ifilter) = (map, filter)
else:
    (imap, ifilter) = (itertools.imap, itertools.ifilter)

class Fortune(callbacks.Plugin):
    """Displays fortunes on a channel in a more flexible way than the
    Unix plugin."""

    def __init__(self, irc):
        self.__parent = super(Fortune, self)
        self.__parent.__init__(irc)
        self.database.plugin = self

        for name in self.registryValue('databases'):
            self.register_database_config(name)

    def format_fortune(self, lines):
        return ' '.join(lines).strip()

    def register_database_config(self, name, url=''):
        conf.registerGlobalValue(conf.supybot.plugins.Fortune.databases, name,
            registry.String(url, _('URL of database %s.') % name))

    class database(callbacks.Commands):
        def add(self, irc, msg, args, name, url):
            """<name> <filename|url>

            Adds a new fortune database."""
            self.plugin.registryValue('databases').add(name)
            self.plugin.register_database_config(name, url)
            irc.replySuccess()
        add = wrap(add, ['owner', 'commandName', first('filename', 'url')])

        def remove(self, irc, msg, args, name):
            """<name>

            Removes a fortune database."""
            if name not in self.plugin.registryValue('databases'):
                irc.error(_('This database does not exist.'), Raise=True)
            self.plugin.registryValue('databases').remove(name)
            conf.supybot.plugins.Fortune.databases.unregister(name)
            irc.replySuccess()
        remove = wrap(remove, ['owner', 'commandName'])

        def list(self, irc, msg, args):
            """takes no arguments

            Returns a list of all known databases."""
            databases = self.plugin.registryValue('databases')
            def formatter(name):
                key = registry.join(['databases', name])
                url = self.plugin.registryValue(key)
                return format('%s %u', name, url)
            items = imap(formatter, databases)
            irc.reply(utils.str.commaAndify(items))

    def read_fortunes(self, name):
        assert name in self.registryValue('databases')
        url = self.registryValue(registry.join(['databases', name]))

        if utils.web.urlRe.match(url):
            fd = utils.web.getUrlFd(url)
        else:
            fd = open(url, 'rb')
        try:
            parts = [[]]
            for line in fd.readlines():
                if line == b'%\n':
                    parts.append([])
                else:
                    for encoding in ('utf8', 'iso-8859-15',
                            utils.web.getEncoding(line)):
                        if encoding is None:
                            continue
                        try:
                            line = line.decode(encoding)
                            break
                        except:
                            continue
                    else:
                        print(repr(line))
                    parts[-1].append(line.strip())
        finally:
            fd.close()
        return parts

    def _search(self, names, pre_pred=None, post_pred=None):
        fortunes = itertools.chain.from_iterable(imap(self.read_fortunes, names))
        if pre_pred:
            fortunes = ifilter(pre_pred, fortunes)
        fortunes = imap(self.format_fortune, fortunes)
        if post_pred:
            fortunes = ifilter(post_pred, fortunes)
        return fortunes

    def sample(self, irc, msg, args, amount, names):
        """[<number>] [<name> [<name> ...]]

        Fetches random fortunes from one of the databases whose name is
        given (uses supybot.plugins.Fortune.defaults.databases as a default).
        """
        channel = msg.args[0]
        names = set(names) or self.registryValue('defaults.databases', channel)
        if not names:
            irc.error(_('No default database configured.'), Raise=True)
        unknown_names = names - self.registryValue('databases')
        if unknown_names:
            irc.error(format(_('This/these databases are unknown: %L'),
                    unknown_names), Raise=True)
        all_fortunes = self._search(names)
        fortunes = random.sample(list(all_fortunes), amount)
        irc.replies(fortunes)
    sample = wrap(sample, ['positiveInt', any('commandName')])

    def random(self, irc, msg, args, max_length, names):
        """[<maxlength>] [<name> [<name> ...]]

        Filters fortunes, and return a random one.
        If maxlength is 0 or not given, defaults to the maximum message
        length.
        """
        channel = msg.args[0]
        # http://tools.ietf.org/html/rfc2812#section-2.3
        # TODO: Adapt to various config options, as irc.reply would.
        max_length = max_length or \
                (510 - len('PRIVMSG %s :%s: ' % (channel, msg.nick)))

        names = set(names) or self.registryValue('defaults.databases', channel)
        if not names:
            irc.error(_('No default database configured.'), Raise=True)
        unknown_names = names - self.registryValue('databases')
        if unknown_names:
            irc.error(format(_('This/these databases are unknown: %L'),
                    unknown_names), Raise=True)

        fortunes = self._search(names, post_pred=lambda x:len(x) < max_length)
        fortunes = list(fortunes)
        if not fortunes:
            irc.error(_('No fortune matched the search.'), Raise=True)
        fortunes = random.choice(fortunes)
        irc.reply(fortunes, noLengthCheck=True)
    random = wrap(random, [optional('nonNegativeInt'), any('commandName')])

Class = Fortune


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
