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

import os
import re
import time

import supybot.log as log
import supybot.conf as conf
import supybot.ircdb as ircdb
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.schedule as schedule
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Eureka')

STATE_STOPPED = 1
STATE_STARTED = 2
STATE_PAUSED = 3

class State:
    def __init__(self, filename):
        self.state = STATE_STOPPED
        self.scores = {}
        filename = os.path.abspath(filename)
        self.fd = open(filename)

    _matchQuestion = re.compile('(?P<value>[0-9]+) (?P<question>.*)')
    _matchClue = re.compile('(?P<delay>[0-9]+) (?P<clue>.*)')
    _matchAnswer = re.compile('(?P<mode>[a-z]) (?P<answer>.*)')
    def loadBlock(self):
        self.question = ''
        self.answers = []
        self.clues = []
        print 1
        for line in self.fd:
            line = line.strip()
            print repr(line)
            if line == '---':
                break
            elif line != '':
                match = self._matchQuestion.match(line)
                if match is None:
                    log.error('Bad Question format for question %r: %r' %
                            (self.question, line))
                    continue
                (value, question) = match.group('value', 'question')
                # We are sure that value is an integer, thanks to the regexp
                self.question = (int(value), question)
        assert self.question != '', 'Missing question.'

        print 2
        for line in self.fd:
            line = line.strip()
            print repr(line)
            if line == '---':
                break
            elif line != '':
                match = self._matchAnswer.match(line)
                if match is None:
                    log.error('Bad answer format for question %r: %r' %
                            (self.question, line))
                    continue
                (mode, answer) = match.group('mode', 'answer')
                if mode != 'r':
                    log.error('Unsupported mode: %r. Only \'r\' (raw)'% mode +
                            'is supported for the moment.')
                    continue
                self.answers.append((mode, answer))

        print 3
        for line in self.fd:
            line = line.strip()
            if line.startswith('=== '):
                self.issue = line[4:]
                try:
                    self.issue = int(self.issue)
                except ValueError:
                    log.error('Bad end of block for question %r: %r' %
                            (self.question, line))
                break
            elif line != '':
                match = self._matchClue.match(line)
                if match is None:
                    log.error('Bad clue format for question %r: %r' %
                            (self.question, line))
                    continue
                (delay, clue) = match.group('delay', 'clue')
                # We are sure that delay is an integer, thanks to the regexp
                self.clues.append((int(delay), clue))

@internationalizeDocstring
class Eureka(callbacks.Plugin):
    """Add the help for "@plugin help Eureka" here
    This should describe *how* to use this plugin."""

    states = {}

    def _ask(self, irc, channel):
        assert channel in self.states, \
                'Asked to ask on a channel where Eureka is not enabled.'
        state = self.states[channel]
        state.loadBlock()
        irc.reply(state.question[1], prefixNick=False)

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        if channel not in self.states:
            return
        reply = None
        state = self.states[channel]
        for mode, answer in state.answers:
            if mode == 'r':
                if msg.args[1] == answer:
                    reply = _('Congratulations %s! The answer was %s.')
                    reply %= (msg.prefix.split('!')[0], answer)
        if reply is not None:
            otherAnswers = [y for x,y in state.answers
                    if x == 'r' and y != msg.args[1]]
            if len(otherAnswers) == 1:
                reply += ' ' + _('Another valid answer is: \'%s\'.')
                reply %= otherAnswers[0]
            elif len(otherAnswers) >= 2:
                reply += ' ' + _('Other valid answers are: \'%s\'.')
                reply %= '\', \''.join([x for x in otherAnswers])
            irc.reply(reply, prefixNick=False)
            self._ask(irc, channel)
                

    @internationalizeDocstring
    def scores(self, irc, msg, args, channel):
        """[<channel>]

        Return the scores on the <channel>. If <channel> is not given, it
        defaults to the current channel."""
        irc.error('Not implemented')
    scores = wrap(scores, ['channel'])

    @internationalizeDocstring
    def score(self, irc, msg, args, channel, nick):
        """[<channel>] <nick>

        Return the score of <nick> on the <channel>. If <channel> is not
        given, it defaults to the current channel."""
        irc.error('Not implemented')
    score = wrap(score, ['nick'])

    @internationalizeDocstring
    def start(self, irc, msg, args, channel):
        """[<channel>]

        Start the Eureka on the given <channel>. If <channel> is not given,
        it defaults to the current channel."""
        self.states[channel] = State(os.path.join(
            conf.supybot.directories.data(), 'Eureka.%s.questions' % channel))
        self._ask(irc, channel)
        # TODO: schedule the first clue
    start = wrap(start, ['op'])

    @internationalizeDocstring
    def stop(self, irc, msg, args, channel):
        """[<channel>]

        Stop the Eureka on the given <channel>. If <channel> is not given,
        it defaults to the current channel."""
        irc.error('Not implemented')
    stop = wrap(stop, ['op'])

    @internationalizeDocstring
    def pause(self, irc, msg, args, channel):
        """[<channel>]

        Pause the Eureka on the given <channel>. If <channel> is not given,
        it defaults to the current channel."""
        irc.error('Not implemented')
    pause = wrap(pause, ['op'])

    @internationalizeDocstring
    def resume(self, irc, msg, args, channel):
        """[<channel>]

        Resume the Eureka on the given <channel>. If <channel> is not given,
        it defaults to the current channel."""
        irc.error('Not implemented')
    resume = wrap(resume, ['op'])

    @internationalizeDocstring
    def adjust(self, irc, msg, args, channel, nick, count):
        """[<channel>] <nick> <number>

        Increase or decrease the score of <nick> on the <channel>.
        If <channel> is not given, it defaults to the current channel."""
        irc.error('Not implemented')
    adjust = wrap(adjust, ['op', 'nick', 'int'])

    @internationalizeDocstring
    def skip(self, irc, msg, args, channel):
        """[<channel>]

        Give up with this question, and switch to the next one."""
        irc.error('Not implemented')
    skip = wrap(skip, ['op'])

Class = Eureka


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
