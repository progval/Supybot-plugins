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

import re
import supybot.conf as conf
import supybot.registry as registry

try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('AttackProtector')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('AttackProtector', True)

class XpY(registry.String):
    """Value must be in the format <number>p<seconds>."""
    _re = re.compile('(?P<number>[0-9]+)p(?P<seconds>[0-9]+)')
    def setValue(self, v):
        if self._re.match(v):
            registry.String.setValue(self, v)
        else:
            self.error()
try:
    XpY = internationalizeDocstring(XpY)
except TypeError:
    # Pypy
    pass

class Punishment(registry.String):
    """Value must be a valid punishment ('ban', 'ban+X', 'kick', 'kban',
    'kban+X', 'mode+X', 'mode-X', 'umode+X', 'umode-X', 'mmode+X', 'mmode-X',
    'command XXX', ...)"""
    def set(self, s):
        if s not in ('ban', 'kick', 'kban') and not s.startswith('mode+') and \
                not s.startswith('mode-') and not s.startswith('umode-') and \
                not s.startswith('umode+') and \
                not s.startswith('mmode+') and not s.startswith('mmode-') and \
                not s.startswith('command ') and \
                not s.startswith('kban+') and not s.startswith('ban+') :
            self.error()
            return
        if s.startswith('kban+') or s.startswith('ban+'):
            try:
                int(s.split('+', 1)[1])
            except ValueError:
                self.error()
                return
        self.setValue(s)
try:
    Punishment = internationalizeDocstring(Punishment)
except TypeError:
    # Pypy
    pass

AttackProtector = conf.registerPlugin('AttackProtector')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(AttackProtector, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))

conf.registerChannelValue(AttackProtector, 'enable',
    registry.Boolean(True, _("""Determines whether or not AttackProtector
    is enabled on this channel.""")))
conf.registerGlobalValue(AttackProtector, 'exempt',
    registry.String('nopunish', _("""If a user has this capability, they
    won't be punished by AttackProtector""")))
conf.registerGlobalValue(AttackProtector, 'kickmessage',
    registry.String(_('$kind flood detected'), _("""The kick message used
    when a user abuses the channel. $kind will be replaced with the kind
    of attack.""")))
conf.registerGlobalValue(AttackProtector, 'delay',
    registry.Integer(10, _("""Determines how long (in seconds) the plugin will
    wait before being enabled. A too low value makes the bot believe that
    its incoming messages 'flood' on connection is an attack.""")))

kinds = {'join': ['5p10', 'ban', ''],
         'knock': ['5p20', 'mode+K', ''],
         'part': ['4p5', 'ban', ''],
         'nick': ['7p300', 'ban', ''],
         'message': ['10p20', 'kick', ''],
         'kicked': ['5p60', 'kban', _('user has been kicked multiple times')],
         'groupjoin': ['20p10', 'mode+i', ''],
         'groupknock': ['7p20', 'mode+K', ''],
         'grouppart': ['20p10', 'mode+i', ''],
         'groupnick': ['20p10', 'mode+N', ''],
         'groupmessage': ['20p20', 'mode+m', '']}
for kind, data in kinds.items():
    detection, punishment, help_ = data
    help_ = help_ or (_('a %s flood is detected') % kind)
    conf.registerGroup(AttackProtector, kind)
    conf.registerChannelValue(getattr(AttackProtector, kind), 'detection',
        XpY(detection, _("""In the format XpY, where X is the number of %s per
        Y seconds that triggers the punishment.""") % kind))
    conf.registerChannelValue(getattr(AttackProtector, kind), 'punishment',
        Punishment(punishment, _("""Determines the punishment applied when
        %s.""") % help_))
    conf.registerChannelValue(getattr(AttackProtector, kind), 'kickmessage',
        registry.String('', _("""The kick message used
        when a user abuses the channel with this kind of flood. If empty,
        defaults to supybot.plugins.AttackProtector.kickmessage.""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
