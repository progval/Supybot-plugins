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
import operator
import threading

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
        self.issue = 0
        filename = os.path.abspath(filename)
        self.fd = open(filename)
        self._waitingForAnswer = threading.Event()

    _matchQuestion = re.compile('(?P<value>[0-9]+) (?P<question>.*)')
    _matchClue = re.compile('(?P<delay>[0-9]+) (?P<clue>.*)')
    _matchAnswer = re.compile('(?P<mode>[a-z]) (?P<answer>.*)')
    def loadBlock(self):
        self._waitingForAnswer.clear()
        self._waitingForAnswer = threading.Event()
        self.question = None
        self.answers = []
        if self.issue is None: # Previous question didn't expire
            for line in self.fd:
                line = line.strip()
                if line.startswith('=== '):
                    break
        self.issue = None
        for line in self.fd:
            line = line.strip()
            if line == '---':
                break
            elif line != '':
                match = self._matchQuestion.match(line)
                if match is None:
                    log.error('Bad question format for question %r: %r' %
                            (self.question, line))
                    continue
                (value, question) = match.group('value', 'question')
                # We are sure that value is an integer, thanks to the regexp
                self.question = (int(value), question)
                self._waitingForAnswer.set()
        if self.question == '':
            self.state = STATE_STOPPED
            return

        for line in self.fd:
            line = line.strip()
            if line == '---':
                break
            elif line != '':
                match = self._matchAnswer.match(line)
                if match is None:
                    log.error('Bad answer format for question %r: %r' %
                            (self.question, line))
                    continue
                (mode, answer) = match.group('mode', 'answer')
                if mode == 'r':
                    pass
                elif mode == 'm':
                    answer = re.compile(answer)
                else:
                    log.error('Unsupported mode: %r. Only \'r\' (raw)'% mode +
                            'is supported for the moment.')
                    continue
                self.answers.append((mode, answer))


    def getClue(self):
        for line in self.fd:
            line = line.strip()
            if line.startswith('=== '):
                try:
                    self.issue = int(line[4:])
                except ValueError:
                    log.error('Bad end of block for question %r: %r' %
                            (self.question, line))
                return (self.issue, None, None) # No more clue
            elif line != '':
                match = self._matchClue.match(line)
                if match is None:
                    log.error('Bad clue format for question %r: %r' %
                            (self.question, line))
                    continue
                (delay, clue) = match.group('delay', 'clue')
                # We are sure that delay is an integer, thanks to the
                # regexp
                return (int(delay), clue, self._waitingForAnswer)

    def adjust(self, nick, count):
        assert isinstance(count, int)
        if nick not in self.scores:
            self.scores[nick] = count
        else:
            self.scores[nick] += count

@internationalizeDocstring
class Eureka(callbacks.Plugin):
    """Add the help for "@plugin help Eureka" here
    This should describe *how* to use this plugin."""

    states = {}

    def _ask(self, irc, channel, now=False):
        assert channel in self.states, \
            'Asked to ask on a channel where Eureka is not enabled.'
        state = self.states[channel]
        def event():
            state.loadBlock()
            if state.question is None:
                state.state = STATE_STOPPED
                return
            irc.reply(state.question[1], prefixNick=False)

            self._giveClue(irc, channel)
        if now:
            event()
        else:
            schedule.addEvent(event, time.time() + state.issue,
                    'Eureka-ask-%s' % channel)

    def _giveClue(self, irc, channel, now=False):
        state = self.states[channel]
        (delay, clue, valid) = state.getClue()
        def event():
            try:
                schedule.removeEvent('Eureka-nextClue-%s' % channel)
            except KeyError:
                pass
            if clue is None:
                assert valid is None
                irc.reply(_('Nobody replied with (one of this) '
                    'answer(s): %s.') %
                    ', '.join([y for x,y in state.answers
                               if x == 'r']),
                    prefixNick=False)
                self._ask(irc, channel)
            else:
                irc.reply(_('Another clue: %s') % clue, prefixNick=False)
                self._giveClue(irc, channel)
        eventName = 'Eureka-nextClue-%s' % channel
        if now and eventName in schedule.schedule.events:
            schedule.schedule.events[eventName]()
            schedule.removeEvent(eventName)
        schedule.addEvent(event, time.time() + delay, eventName)

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        nick = msg.prefix.split('!')[0]
        if channel not in self.states:
            return
        reply = None
        state = self.states[channel]
        for mode, answer in state.answers:
            if mode == 'r':
                if msg.args[1].lower() == answer.lower():
                    state.adjust(nick, state.question[0])
                    reply = _('Congratulations %s! The answer was %s.')
                    reply %= (nick, answer)
            elif mode == 'm':
                if answer.match(msg.args[1]):
                    state.adjust(nick, state.question[0])
                    reply = _('Congratulations %s! The answer was %s.')
                    reply %= (nick, msg.args[1])
        if reply is not None:
            schedule.removeEvent('Eureka-nextClue-%s' % channel)
            otherAnswers = [y for x,y in state.answers
                    if x == 'r' and y.lower() != msg.args[1].lower()]
            if len(otherAnswers) == 1:
                reply += ' ' + _('Another valid answer is: \'%s\'.')
                reply %= otherAnswers[0]
            elif len(otherAnswers) >= 2:
                reply += ' ' + _('Other valid answers are: \'%s\'.')
                reply %= '\', \''.join([x for x in otherAnswers])
            irc.reply(reply, prefixNick=False)
            self._ask(irc, channel, True)


    @internationalizeDocstring
    def scores(self, irc, msg, args, channel):
        """[<channel>]

        Return the scores on the <channel>. If <channel> is not given, it
        defaults to the current channel."""
        if channel not in self.states:
            irc.error(_('Eureka is not enabled on this channel'))
            return
        scores = self.states[channel].scores.items()
        if scores == []:
            irc.reply(_('Noone played yet.'))
        else:
            scores.sort(key=operator.itemgetter(1))
            scores.reverse()
            irc.reply(', '.join(['%s(%i)' % x for x in scores]))
    scores = wrap(scores, ['channel'])

    @internationalizeDocstring
    def score(self, irc, msg, args, channel, nick):
        """[<channel>] <nick>

        Return the score of <nick> on the <channel>. If <channel> is not
        given, it defaults to the current channel."""
        if channel not in self.states:
            irc.error(_('Eureka is not enabled on this channel'))
            return
        state = self.states[channel]
        if nick not in state.scores:
            irc.error(_('This user did not play yet.'))
            return
        irc.reply(str(state.scores[nick]))
    score = wrap(score, ['channel', 'nick'])

    @internationalizeDocstring
    def start(self, irc, msg, args, channel):
        """[<channel>]

        Start the Eureka on the given <channel>. If <channel> is not given,
        it defaults to the current channel."""
        if channel in self.states and \
                self.states[channel].state != STATE_STOPPED:
            irc.error(_('Eureka is already enabled on this channel'))
            return
        state = State(os.path.join(conf.supybot.directories.data(),
            'Eureka.%s.questions' % channel))
        state.state = STATE_STARTED
        self.states[channel] = state
        self._ask(irc, channel, True)
    start = wrap(start, ['op'])

    @internationalizeDocstring
    def stop(self, irc, msg, args, channel):
        """[<channel>]

        Stop the Eureka on the given <channel>. If <channel> is not given,
        it defaults to the current channel."""
        if channel not in self.states or \
                self.states[channel].state == STATE_STOPPED:
            irc.error(_('Eureka is not enabled on this channel'))
            return
        self.states[channel].state = STATE_STOPPED
        schedule.removeEvent('Eureka-nextClue-%s' % channel)
        irc.replySuccess()
    stop = wrap(stop, ['op'])

    @internationalizeDocstring
    def pause(self, irc, msg, args, channel):
        """[<channel>]

        Pause the Eureka on the given <channel>. If <channel> is not given,
        it defaults to the current channel."""
        if channel not in self.states or \
                self.states[channel].state == STATE_STOPPED:
            irc.error(_('Eureka is not enabled on this channel'))
            return
        state = self.states[channel]
        if state.state == STATE_PAUSED:
            irc.error(_('Eureka is already paused.'))
            return
        state.state = STATE_PAUSED
        schedule.removeEvent('Eureka-nextClue-%s' % channel)
        irc.replySuccess()
    pause = wrap(pause, ['op'])

    @internationalizeDocstring
    def resume(self, irc, msg, args, channel):
        """[<channel>]

        Resume the Eureka on the given <channel>. If <channel> is not given,
        it defaults to the current channel."""
        if channel not in self.states or \
                self.states[channel].state == STATE_STOPPED:
            irc.error(_('Eureka is not enabled on this channel'))
            return
        state = self.states[channel]
        if state.state != STATE_PAUSED:
            irc.error(_('Eureka is not paused.'))
            return
        state.state = STATE_STARTED
        self._giveClue(irc, channel, True)
    resume = wrap(resume, ['op'])

    @internationalizeDocstring
    def adjust(self, irc, msg, args, channel, nick, count):
        """[<channel>] <nick> <number>

        Increase or decrease the score of <nick> on the <channel>.
        If <channel> is not given, it defaults to the current channel."""
        self.states[channel].adjust(nick, count)
        irc.replySuccess()
    adjust = wrap(adjust, ['op', 'nick', 'int'])

    @internationalizeDocstring
    def skip(self, irc, msg, args, channel):
        """[<channel>]

        Give up with this question, and switch to the next one."""
        if channel not in self.states or \
                self.states[channel].state == STATE_STOPPED:
            irc.error(_('Eureka is not enabled on this channel'))
            return
        try:
            schedule.removeEvent('Eureka-nextClue-%s' % channel)
        except KeyError:
            pass
        self._ask(irc, channel, True)
    skip = wrap(skip, ['op'])

    @internationalizeDocstring
    def clue(self, irc, msg, args, channel):
        """[<channel>]

        Give the next clue."""
        self._giveClue(irc, channel, True)
    clue = wrap(clue, ['op'])

Class = Eureka


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
