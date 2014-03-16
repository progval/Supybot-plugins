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

import json
import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NoisyKarma')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('NoisyKarma', True)

def value_validator(value):
    if not isinstance(value, list):
        return _('Dict key must be a list')
    for subvalue in value:
        if not isinstance(subvalue, dict):
            return _('List items must be dicts.')
        if set(value.keys()) != set(['action', 'message']):
            return _('List items must be dicts with "action" and "message" '
                    'as keys.')
    return None

class KarmaMessages(registry.Json):
    def set(self, v):
        try:
            data = json.loads(v)
        except ValueError:
            self.error(_('Value must be json data.'))
            return
        if not isinstance(data, dict):
            self.error(_('Value must be a json dict.'))
            return
        if any(map(lambda x:not isinstance(x, int), data.keys())):
            self.error(_('Dict keys must be integers.'))
            return
        if any(map(lambda x:x<=0, data.keys())):
            self.error(_('Dict keys must be non-negative integers.'))
            return
        errors = list(filter(bool, map(value_validator, data.values())))
        if errors:
            self.error(errors[0])
            return
        self.setValue(data)

NoisyKarma = conf.registerPlugin('NoisyKarma')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(NoisyKarma, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))
conf.registerGroup(NoisyKarma, 'messages')
conf.registerChannelValue(NoisyKarma.messages, 'positive',
    KarmaMessages({}, _("""Messages shown for things with positive karma.
    For a given karma, the message with the closest key to the karma will
    be selected, among messages with a key greater than the karma.""")))
conf.registerChannelValue(NoisyKarma.messages, 'negative',
    KarmaMessages({}, _("""Messages shown for things with negative karma.
    For a given absolute karma, the message with the closest key to the
    karma will be selected, among messages with an absolute key greater
    than the absolute karma""")))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
