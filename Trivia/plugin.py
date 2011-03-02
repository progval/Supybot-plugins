###
# Copyright (c) 2010, quantumlemur
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
import os
import time
import math
import string
import random
import supybot.utils as utils
import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.schedule as schedule
import supybot.callbacks as callbacks


class Trivia(callbacks.Plugin):
    """Add the help for "@plugin help Trivia" here
    This should describe *how* to use this plugin."""
    threaded = True

    
    def __init__(self, irc):
        self.__parent = super(Trivia, self)
        self.__parent.__init__(irc)
        self.games = {}
        self.scores = {}
        questionfile = self.registryValue('questionFile')
        if not os.path.exists(questionfile):
            f = open(questionfile, 'w')
            f.write('If you\'re seeing this question, it means that the questions file that you specified wasn\'t found, and a new one has been created.  Go get some questions!%sNo questions found' % self.registryValue('questionFileSeparator'))
            f.close()
        self.scorefile = self.registryValue('scoreFile')
        if not os.path.exists(self.scorefile):
            f = open(self.scorefile, 'w')
            f.close()
        f = open(self.scorefile, 'r')
        line = f.readline()
        while line:
            (name, score) = line.split(' ')
            self.scores[name] = int(score.strip('\r\n'))
            line = f.readline()
        f.close()


    def doPrivmsg(self, irc, msg):
        channel = ircutils.toLower(msg.args[0])
        if not irc.isChannel(channel):
            return
        if callbacks.addressed(irc.nick, msg):
            return
        if channel in self.games:
            self.games[channel].answer(msg)

    
    class Game:
        def __init__(self, irc, channel, num, registryValue, games, scores, scorefile):
            self.rng = random.Random()
            self.rng.seed()
            self.registryValue = registryValue
            self.irc = irc
            self.channel = channel
            self.num = num
            self.numAsked = 0
            self.hints = 0
            self.games = games
            self.scores = scores
            self.scorefile = scorefile
            self.questionfile = self.registryValue('questionFile')
            self.total = num
            self.active = True
            self.questions = []
            self.roundscores = {}
            self.unanswered = 0
            f = open(self.questionfile, 'r')
            line = f.readline()
            while line:
                self.questions.append(line.strip('\n\r'))
                line = f.readline()
            f.close()
            try:
                schedule.removeEvent('next_%s' % self.channel)
            except KeyError:
                pass
            self.newquestion()
       

        def newquestion(self):
            if self.num == 0:
                self.active = False
            elif self.unanswered > self.registryValue('inactiveShutoff', self.channel)  and self.registryValue('inactiveShutoff', self.channel) >= 0:
                self.reply('Seems like no one\'s playing any more.')
                self.active = False
            elif len(self.questions) == 0:
                self.reply('Oops!  I ran out of questions!')
                self.active = False
            if not self.active:
                self.stop()
                return
            self.hints = 0
            self.num -= 1
            self.numAsked += 1
            which = self.rng.randint(0, len(self.questions)-1)
            q = self.questions.pop(which)
            sep = self.registryValue('questionFileSeparator')
            self.q = q[:q.find(sep)]
            self.a = q[q.find(sep)+len(sep):].split(sep)
            self.reply('\x03%s#%d of %d: %s' % (self.registryValue('color', self.channel), self.numAsked, self.total, self.q))
            def event():
                self.timedEvent()
            eventTime = time.time() + self.registryValue('timeout', self.channel) / (self.registryValue('numHints', self.channel) + 1)
            if self.active:
                schedule.addEvent(event, eventTime, 'next_%s' % self.channel)


        def stop(self):
            self.reply('Trivia stopping.')
            self.active = False
            try:
                schedule.removeEvent('next_%s' % self.channel)
            except KeyError:
                pass
            scores = self.roundscores.iteritems()
            sorted = []
            for i in range(0, len(self.roundscores)):
                item = scores.next()
                sorted.append(item)
            def cmp(a, b):
                return b[1] - a[1]
            sorted.sort(cmp)
            max = 3
            if len(sorted) < max:
                max = len(sorted)
#                self.reply('max: %d.  len: %d' % (max, len(sorted)))
            s = 'Top finishers: '
            if max > 0:
                recipients = []
                maxp = sorted[0][1]
                for i in range(0, max):
                    item = sorted[i]
                    s = '%s %s %s.' % (s, item[0], item[1])
                self.reply(s)
            del self.games[self.channel]
        

        def timedEvent(self):
            if self.hints >= self.registryValue('numHints', self.channel):
                self.reply('No one got the answer!  It was: %s' % self.a[0])
                self.unanswered += 1
                self.newquestion()
            else:
                self.hint()


        def hint(self):
            self.hints += 1
            ans = self.a[0]
            divider = int( math.ceil( len(ans) * self.registryValue('hintPercentage', self.channel) * self.hints ) )
            if divider == len(ans):
                divider -= 1
            show = ans[ : divider]
            blank = ans[divider : ]
            blank = re.sub('\w', self.registryValue('blankChar', self.channel), blank)
            self.reply('HINT: %s%s' % (show, blank))
            def event():
                self.timedEvent()
            eventTime = time.time() + self.registryValue('timeout', self.channel) / (self.registryValue('numHints', self.channel)+1)
            if self.active:
                schedule.addEvent(event, eventTime, 'next_%s' % self.channel)


        def answer(self, msg):
            correct = False
            for ans in self.a:
                dist = self.DL(str.lower(msg.args[1]), str.lower(ans))
                if dist <= len(ans)/self.registryValue('flexibility', self.channel):
                    correct = True
#                if self.registryValue('debug'):
#                    self.reply('Distance: %d' % dist)
            if correct:
                if not msg.nick in self.scores:
                    self.scores[msg.nick] = 0
                self.scores[msg.nick] += 1
                if not msg.nick in self.roundscores:
                    self.roundscores[msg.nick] = 0
                self.roundscores[msg.nick] += 1
                self.unanswered = 0
                self.reply('%s got it!  The full answer was: %s.  Points: %d' % (msg.nick, self.a[0], self.scores[msg.nick]))
                schedule.removeEvent('next_%s' % self.channel)
                self.writeScores()
                self.newquestion()


        def reply(self, s):
            self.irc.queueMsg(ircmsgs.privmsg(self.channel, s))


        def writeScores(self):
            f = open(self.scorefile, 'w')
            scores = self.scores.iteritems()
            for i in range(0, len(self.scores)):
                score = scores.next()
                f.write('%s %s\n' % (score[0], score[1]))
            f.close()


        def DL(self, seq1, seq2):
            oneago = None
            thisrow = range(1, len(seq2) + 1) + [0]
            for x in xrange(len(seq1)):
                # Python lists wrap around for negative indices, so put the
                # leftmost column at the *end* of the list. This matches with
                # the zero-indexed strings and saves extra calculation.
                twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
                for y in xrange(len(seq2)):
                    delcost = oneago[y] + 1
                    addcost = thisrow[y - 1] + 1
                    subcost = oneago[y - 1] + (seq1[x] != seq2[y])
                    thisrow[y] = min(delcost, addcost, subcost)
                    # This block deals with transpositions
                    if (x > 0 and y > 0 and seq1[x] == seq2[y - 1] and seq1[x-1] == seq2[y] and seq1[x] != seq2[y]):
                        thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)
            return thisrow[len(seq2) - 1]


    def trivia(self, irc, msg, args, channel, num):
        """[<channel>] [<number of questions>]

        Starts a game of trivia.  <channel> is only necessary if the message isn't sent in the channel itself."""
        if num == None:
            num = self.registryValue('defaultRoundLength', channel)
#        elif num > 100:
#            irc.reply('sorry, for now, you can\'t start games with more than 100 questions :(')
#            num = 100
        channel = ircutils.toLower(channel)
        if channel in self.games:
            if not self.games[channel].active:
                del self.games[channel]
                try:
                    schedule.removeEvent('next_%s' % channel)
                except KeyError:
                    pass
                irc.reply('Orphaned trivia game found and removed.')
            else:
                self.games[channel].num += num
                self.games[channel].total += num
                irc.reply('%d questions added to active game!' % num)
        else:
            self.games[channel] = self.Game(irc, channel, num, self.registryValue, self.games, self.scores, self.scorefile)
        irc.noReply()
    trivia = wrap(trivia, ['channel', optional('positiveInt')])


    def strivia(self, irc, msg, args, channel):
        """[<channel>]

        Stops a running game of trivia.  <channel> is only necessary if the message isn't sent in the channel itself."""
        channel = ircutils.toLower(channel)
        try:
            schedule.removeEvent('next_%s' % channel)
        except KeyError:
            pass
        if channel in self.games:
            if self.games[channel].active:
                self.games[channel].stop()
            else:
                del self.games[channel]
                irc.reply('Trivia stopped')
        else:
            irc.noReply()
    strivia = wrap(strivia, ['channel'])    
   

Class = Trivia


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
