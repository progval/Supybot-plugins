# coding: utf8
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
import functools

import supybot.conf as conf
import supybot.world as world
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

MATCH_MESSAGE_STRIPNICK = re.compile('^(<[^ ]+> )?(?P<message>.*)$')

CHANNELLOGER_REGEXP_BASE = re.compile('^[^ ]*  (<[^ ]+> )?(?P<message>.*)$')
CHANNELLOGER_REGEXP_STRIPNICK = re.compile('^[^ ]*  (<[^ ]+> )?(<[^ ]+> )?(?P<message>.*)$')

def get_channelloger_extracter(stripRelayedNick):
    @markovgen.mixed_encoding_extracting
    def channelloger_extracter(x):
        regexp = CHANNELLOGER_REGEXP_STRIPNICK if stripRelayedNick else \
                CHANNELLOGER_REGEXP_BASE
        m = regexp.match(x)
        if m:
            return m.group('message')
    return channelloger_extracter

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
        extracter = get_channelloger_extracter(
                self.registryValue('stripRelayedNick', channel))
        for irc in world.ircs:
            for filename in glob.glob(cb.getLogDir(irc, channel) + '/*.log'):
                with open(filename, 'rb') as fd:
                    m.feed_from_file(fd, extracter)

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
        if not self.registryValue('enable', channel):
            return
        m = self._get_markov(irc, channel)
        if self.registryValue('stripRelayedNick', channel):
            message = MATCH_MESSAGE_STRIPNICK.match(message).group('message')
        m.feed(message)
        if random.random() < self.registryValue('probability', channel):
            self._answer(irc, message, m, False)

    @wrap(['channel', optional('text')])
    def gen(self, irc, msg, args, channel, message):
        """[<channel>] <seed>

        Generates a random message based on the logs of a channel
        and a seed"""
        if not self.registryValue('enable', channel):
            irc.error(_('Markovgen is disabled for this channel.'),
                    Raise=True)
        m = self._get_markov(irc, channel)
        m.feed(message)
        self._answer(irc, message, m, True)


    def _answer(self, irc, message, m, allow_duplicate):
        words = message.split(' ')
        message_tuples = set(zip(words, words[1:]))
        if not message_tuples:
            return
        seeds = list(m.available_seeds())
        possibilities = [x for x in seeds if x in message_tuples]
        seed = list(random.choice(possibilities))
        backward_seed = list(reversed(seed))
        forward = m.generate_markov_text(seed=seed, backward=False)
        backward = m.generate_markov_text(seed=backward_seed,
                backward=True)
        try:
            answer = '%s %s' % (backward, forward.split(' ', 2)[2])
        except IndexError:
            answer = backward
        if allow_duplicate or m != answer:
            irc.reply(answer, prefixNick=False)

    @wrap(['channel'])
    def doge(self, irc, msg, args, channel):
        """takes no arguments

        Generates a doge."""
        if not self.registryValue('enable', channel):
            irc.error(_('Markovgen is disabled for this channel.'),
                    Raise=True)
        r = re.compile('^[a-zA-Zéèàù]{5,}$')
        def pred(x):
            if not r.match(x):
                return None
            else:
                return x
        m = self._get_markov(irc, channel)
        words = m.words
        words = filter(bool, map(pred, words))
        words = [x.strip(',?;.:/!') for x in m.words if pred(x)]
        w2 = random.choice(words)
        w1 = random.choice(['such', 'many', 'very'])
        irc.reply('%s %s' % (w1, w2))


Class = Markovgen


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
