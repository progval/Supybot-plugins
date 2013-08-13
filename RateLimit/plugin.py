###
# Copyright (c) 2013, Valentin Lorentz
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

import time

import supybot.dbi as dbi
import supybot.conf as conf
import supybot.utils as utils
import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('RateLimit')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

if not hasattr(callbacks.Commands, 'pre_command_callbacks'):
    raise callbacks.Error(
            'Your version of Supybot is not compatible with '
            'this plugin (it does not have support for '
            'pre-command-call callbacks).')

class RateLimitRecord(dbi.Record):
    __fields__ = ('channel', 'user', 'count', 'interval', 'command')
class RateLimitDB(dbi.DB):
    Record = RateLimitRecord
    def set_user_limit(self, channel, user, count, interval, command):
        record = RateLimitRecord(channel=channel, user=user, count=count,
                interval=interval, command=command)
        try:
            previous_record = list(filter(
                    lambda x:x.user == user and
                             x.command == command and
                             x.channel == channel,
                    self))[0]
        except IndexError:
            self.add(record)
        else:
            self.set(previous_record.id, record)

    def get_limits(self, command):
        return filter(lambda x:x.command == command, self)
    def get_user_limit(self, user, command):
        records = list(filter(lambda x:x.user in (user, '*', 'global'),
                         self.get_limits(command)))
        # TODO: Add channel support.
        try:
            return list(filter(lambda x:x.user == user, records))[0]
        except IndexError:
            return list(records)[0] # May raise IndexError too

filename = conf.supybot.directories.data.dirize('RateLimit.db')

def format_ratelimit(record):
    return _('%(count)s per %(interval)s sec') % {
            'count': record.count,
            'interval': record.interval
            }

class RateLimit(callbacks.Plugin):
    """Add the help for "@plugin help RateLimit" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        super(RateLimit, self).__init__(irc)
        self.db = RateLimitDB(filename)
        callbacks.Commands.pre_command_callbacks.append(
                self._pre_command_callback)
        self._history = {} # {command: [(user, timestamp)]}

    def die(self):
        callbacks.Commands.pre_command_callbacks.remove(
                self._pre_command_callback)

    def _pre_command_callback(self, command, irc, msg, *args, **kwargs):
        command = ' '.join(command)
        try:
            user = ircdb.users.getUserId(msg.prefix)
        except KeyError:
            user = None
        try:
            record = self.db.get_user_limit(user, command)
        except IndexError:
            return False
        else:
            if command not in self._history:
                list_ = []
                self._history[command] = list_
            else:
                list_ = self._history[command]
            timestamp = time.time() - record.interval
            list_ = list(filter(lambda x:x[1] > timestamp and
                                         (x[0]==user or record.user=='global'),
                                list_))
            if len(list_) >= record.count:
                self.log.info('Throttling command %r call (rate limited).',
                        command)
                return True
            list_.append((user, time.time()))
            self._history[command] = list_
            return False

    @wrap([optional(first('otherUser', ('literal', '*'))),
        'nonNegativeInt', 'nonNegativeInt', 'commandName', 'admin'])
    def set(self, irc, msg, args, user, count, interval, command):
        """[<user>] <how many in interval> <interval length> <command>

        Sets the rate limit of the <command> for the <user>.
        If <user> is not given, the rate limit will be enforced globally,
        and if * is given as the <user>, the rate limit will be enforced
        for everyone."""
        if user is None:
            user = 'global'
        elif user != '*':
            user = user.id
        self.db.set_user_limit(None, user, count, interval, command)
        irc.replySuccess()

    @wrap(['commandName'])
    def get(self, irc, msg, args, command):
        """<command>

        Return rate limits set for the given <command>."""
        records = self.db.get_limits(command)
        global_ = 'none'
        star = 'none'
        users = []
        for record in records:
            if record.user == 'global':
                global_ = format_ratelimit(record)
            elif record.user == '*':
                star = format_ratelimit(record)
            else:
                users.append('%s: %s' % (ircdb.users.getUser(record.user).name,
                                         format_ratelimit(record)))
        irc.reply(', '.join([_('global: %s') % global_,
                             _('*: %s') % star] +
                            users))



Class = RateLimit


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
