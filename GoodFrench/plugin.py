# -*- coding: utf8 -*-
###
# Copyright (c) 2010, Valentin Lorentz
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

import config
reload(config)

import re
import supybot.world as world
import supybot.ircmsgs as ircmsgs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

class SpellChecker:
    def __init__(self, text, level):
        # 0 : pas de filtrage ;
        # 1 : filtre le langage SMS
        # 2 : filtre les erreurs de pluriel ;
        # 3 : filtre les fautes de conjugaison courantes ;
        # 4 : filtre les fautes d'orthographe courantes ;
        # 5 : filtre les abbréviations ("t'as" au lieu de "tu as")
        self._text = text
        self._errors = []
        if level >= 1:
            self._checking = 'SMS'
            self.checkSMS()
        if level >= 2:
            self._checking = 'pluriel'
            self.checkPlural()
        if level >= 3:
            self._checking = 'conjugaison'
            self.checkConjugaison()
        if level >= 4:
            self._checking = 'orthographe'
            self.checkSpelling()
        if level >= 5:
            self._checking = 'abbréviation'
            self.checkAbbreviation()
        if level >= 6:
            self._checking = 'lol'
            self.checkLol()
        if level >= 7:
            self._checking = 'typographie'
            self.checkTypographic()

    def _raise(self, message):
        self._errors.append('[%s] %s' % (self._checking, message))

    def _detect(self, mode, correct, mask, displayedMask=None, wizard=' '):
        if displayedMask is None:
            displayedMask = mask
        raise_ = False
        text = self._text
        nickRemover = re.match('[^ ]*: (?P<text>.*)', text)
        if nickRemover is not None:
            text = nickRemover.group('text')
        text = '%s%s%s' % (wizard, text, wizard)
        AntislashDoubleYou = '[^a-zA-Z0-9éèàùâêûôîäëüïö\']'
        if mode == 'single' and re.match('.*%s%s%s.*' % (AntislashDoubleYou,
                                                        mask,
                                                        AntislashDoubleYou),
                                         text, re.IGNORECASE) is not None:
            raise_ = True
        elif mode == 'regexp' and re.match('.*%s.*' % mask, text):
            raise_ = True

        if raise_:
            if self._checking == 'conjugaison' or \
            self._checking == 'typographie':
                self._raise(correct)
            else:
                if correct.__class__ == list:
                    correct = '`%s`' % '`, ou `'.join(correct)
                else:
                    correct = '`%s`' % correct

                if displayedMask.__class__ == list:
                    displayedMask = '`%s`' % '` ou `'.join(displayedMask)
                else:
                    displayedMask = '`%s`' % displayedMask
                self._raise('On ne dit pas %s mais %s' %
                           (displayedMask, correct))

    def checkSMS(self):
        bad = {
                't': 't\'es',
                'ki': 'qui',
                'koi': 'quoi',
                'tqvu': 't\'as vu',
                'tt': 'tout',
                'ct': 'c\'était',
                'v': 'vais',
                'twa': 'toi',
                'toa': 'toi',
                'mwa': 'moi',
                'moa': 'moi',
                'tro': 'trop',
                'bi1': 'bien',
                'çay': 'c\'est',
                'fé': ['fais', 'fait'],
                'm': ['aime', 'aimes', 'aiment'],
                'u': ['eu', 'eut'],
            }
        for mask, correct in bad.items():
            self._detect(mode='single', correct=correct, mask=mask)

        self._detect(mode='regexp', correct="c'est",
                     mask="(?<!(du|Du|le|Le|en|En)) C (?<!c')",
                     displayedMask='C')

    def checkPlural(self):
        pass
    def checkConjugaison(self):
        self._detect(mode='regexp', correct="t'as oublié un `ne` ou un `n'`",
                     mask="(je|tu|on|il|elle|nous|vous|ils|elles) [^' ]+ pas ")
        self._detect(mode='regexp', correct="t'as oublié un `ne` ou un `n'`",
                     mask="j'[^' ]+ pas")
        firstPerson = 'un verbe à la première personne ne finit pas par un `t`'
        notAS = 'ce verbe ne devrait pas se finir par un `s` à cette personne.'
        self._detect(mode='regexp', correct=firstPerson, mask="j'[^ ]*t\W")
        self._detect(mode='regexp', correct=firstPerson,mask="je( ne)? [^ ]*t\W")
        self._detect(mode='regexp', correct=notAS,
                     mask=" (il|elle|on)( ne | n'| )[^ ]*[^u]s\W")
                     # [^u] is added in order to not detect 'il [vn]ous...'
    def checkSpelling(self):
        self._detect(mode='regexp', correct='quelle', mask='quel [^ ]+ la',
                     displayedMask='quel')
        self._detect(mode='regexp', correct='quel', mask='quelle [^ ]+ le',
                     displayedMask='quelle')
        self._detect(mode='regexp', correct=['quels', 'quelles'],
                     mask='quel [^ ]+ les',
                     displayedMask='quel')
        self._detect(mode='regexp', correct=['quels', 'quelles'],
                     mask='quelle [^ ]+ les',
                     displayedMask='quelle')
        self._detect(mode='single',
                     correct=['quel', 'quels', 'quelle', 'quelles'],
                     mask='kel')
        self._detect(mode='single',
                     correct=['quel', 'quels', 'quelle', 'quelles'],
                     mask='kelle')
        self._detect(mode='single',
                     correct=['quel', 'quels', 'quelle', 'quelles'],
                     mask='kels')
        self._detect(mode='single',
                     correct=['quel', 'quels', 'quelle', 'quelles'],
                     mask='kelles')
    def checkAbbreviation(self):
        pass
    def checkLol(self):
        self._detect(mode='regexp', correct='mdr', mask='[Ll1][oO0iu]+[lL1]',
                     displayedMask='lol')
        self._detect(mode='regexp', correct='mdr', mask=' [Ll1] +[lL1] ',
                     displayedMask='lol')
    def checkTypographic(self):
        self._detect(mode='regexp',
                     correct="Un caractère de ponctuation double est toujours "
                     "précédé d'un espace",
                     mask="[^ _D()][:!?;][^/]", wizard='_')
        self._detect(mode='regexp',
                     correct="Un caractère de ponctuation double est toujours "
                     "suivi d'un espace",
                     mask="(?<!(tp|ps|.[^ a-zA-Z]))[:!?;][^ _'D()]", wizard='_')
        self._detect(mode='regexp',
                     correct="Un caractère de ponctuation simple n'est jamais "
                     "précédé d'un espace",
                     mask=" ,", wizard='_')
        self._detect(mode='regexp',
                     correct="Un caractère de ponctuation simple est toujours "
                     "suivi d'un espace",
                     mask=",[^ _]", wizard='_')

    def getErrors(self):
        return self._errors

class GoodFrench(callbacks.Plugin):
    def detect(self, irc, msg, args, text):
        """<texte>

        Cherche des fautes dans le <texte>, en fonction de la valeur locale de
        supybot.plugins.GoodFrench.level."""
        checker = SpellChecker(text, self.registryValue('level', msg.args[0]))
        errors = checker.getErrors()
        if len(errors) == 0:
            irc.reply('La phrase semble correcte')
        elif len(errors) == 1:
            irc.reply('Il semble y avoir une erreur : %s' % errors[0])
        else:
            irc.reply('Il semble y avoir des erreurs : %s' %
                      ' | '.join(errors))
    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        text = msg.args[1]
        prefix = msg.prefix
        nick = prefix.split('!')[0]
        if callbacks.addressed(irc.nick, msg): #message is direct command
            return

        checker = SpellChecker(text, self.registryValue('level', channel))
        errors = checker.getErrors()
        if len(errors) == 0:
            return
        elif len(errors) == 1:
            reason = 'Erreur : %s' % errors[0]
        else:
            reason = 'Erreurs : %s' % ' | '.join(errors)
        if self.registryValue('kick'):
            msg = ircmsgs.kick(channel, nick, reason)
            irc.queueMsg(msg)
        else:
            irc.reply(reason)

    detect = wrap(detect, ['text'])


Class = GoodFrench


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
