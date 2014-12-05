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

import re
import glob
import random

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Markovgen')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

try:
    import markovgen
except ImportError:
    raise callbacks.Error('Cannot load markovgen library. Make sure you '
                          'installed it.')
from imp import reload as r
r(markovgen)

CHANNELLOGER_REGEXP = re.compile('^[^ ]*  (<[^ ]+> )?(?P<message>.*)$')
@markovgen.mixed_encoding_extracting
def channelloger_extracter(x):
    m = CHANNELLOGER_REGEXP.match(x)
    if m:
        return m.group('message')

class Markovgen(callbacks.Plugin):
    """Add the help for "@plugin help Markovgen" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        super(Markovgen, self).__init__(irc)
        self._markovs = {}

    def _load_from_channellogger(self, irc, channel, m):
        cb = irc.getCallback('ChannelLogger')
        if not cb:
            return
        for filename in glob.glob(cb.getLogDir(irc, channel) + '/*.log'):
            with open(filename, 'rb') as fd:
                m.feed_from_file(fd, channelloger_extracter)

    def _get_markov(self, irc, channel):
        if channel not in self._markovs:
            m = markovgen.Markov()
            self._markovs[channel] = m
            self._load_from_channellogger(irc, channel, m)
        else:
            m = self._markovs[channel]
        return m

    def doPrivmsg(self, irc, msg):
        (channel, message) = msg.args
        if not irc.isChannel(channel):
            return
        probability = self.registryValue('probability', channel)
        if probability == 0:
            return
        m = self._get_markov(irc, channel)
        m.feed(message)
        if random.random() < probability:
            self._answer(irc, message, m)

    @wrap(['channel', 'text'])
    def gen(self, irc, msg, args, channel, message):
        """[<channel>] <seed>

        Generates a random message based on the logs of a channel
        and a seed"""
        probability = self.registryValue('probability', channel)
        if probability == 0:
            irc.error(_('Markovgen is disabled for this channel.'))
        m = self._get_markov(irc, channel)
        m.feed(message)
        self._answer(irc, message, m)


    def _answer(self, irc, message, m):
        words = message.split(' ')
        message_tuples = set(zip(words, words[1:]))
        if not message_tuples:
            return
        possibilities = [x for x in m.available_seeds() if x in message_tuples]
        seed = list(random.choice(possibilities))
        backward_seed = list(reversed(seed))
        forward = m.generate_markov_text(seed=seed, backward=False)
        backward = m.generate_markov_text(seed=backward_seed,
                backward=True)
        try:
            answer = '%s %s' % (backward, forward.split(' ', 2)[2])
        except IndexError:
            answer = backward
        irc.reply(answer, prefixNick=False)



Class = Markovgen


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
