###
# Copyright (c) 2010, quantumlemur
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

import supybot.conf as conf
import supybot.registry as registry
from supybot.i18n import PluginInternationalization, internationalizeDocstring
_ = PluginInternationalization('Trivia')
def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Trivia', True)


Trivia = conf.registerPlugin('Trivia')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Trivia, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))

conf.registerChannelValue(Trivia, 'blankChar',
        registry.String('*', _("""The character used for a blank when
        displaying hints""")))

conf.registerChannelValue(Trivia, 'numHints',
        registry.PositiveInteger(3, _("""The number of hints to be given for
        each question""")))

conf.registerChannelValue(Trivia, 'timeout',
        registry.PositiveInteger(90, _("""The number of seconds to allow for
        each question""")))

conf.registerChannelValue(Trivia, 'hintPercentage',
        registry.Probability(0.25, _("""The fraction of the answer that
        should be revealed with each hint""")))

conf.registerChannelValue(Trivia, 'flexibility',
        registry.PositiveInteger(8, _("""The flexibility of the trivia answer
        checker.  One typo will be allowed for every __ characters.""")))

conf.registerChannelValue(Trivia, 'color',
        registry.PositiveInteger(10, _("""The mIRC color to use for trivia
        questions""")))

conf.registerChannelValue(Trivia, 'inactiveShutoff',
        registry.Integer(6, _("""The number of questions that can go
        unanswered before the trivia stops automatically.""")))

conf.registerGlobalValue(Trivia, 'scoreFile',
        registry.String('scores.txt', _("""The path to the scores file.
        If it doesn't exist, it will be created.""")))

conf.registerGlobalValue(Trivia, 'questionFile',
        registry.String('questions.txt', _("""The path to the questions file.
        If it doesn't exist, it will be created.""")))

conf.registerChannelValue(Trivia, 'defaultRoundLength',
        registry.PositiveInteger(10, _("""The default number of questions to
        be asked in a round of trivia.""")))

conf.registerGlobalValue(Trivia, 'questionFileSeparator',
        registry.String('*', _("""The separator used between the questions
        and answers in your trivia file.""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
