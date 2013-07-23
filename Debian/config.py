###
# Copyright (c) 2003-2005, James Vega
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
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('AttackProtector')
except:
    _ = lambda x:x

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import output, expect, anything, something, yn
    conf.registerPlugin('Debian', True)

class ValidBranch(registry.OnlySomeStrings):
    validStrings = ('oldstable', 'stable', 'testing', 'unstable',
            'experimental')
class ValidMode(registry.OnlySomeStrings):
    validStrings = ('path', 'exactfilename', 'filename')
class ValidSection(registry.OnlySomeStrings):
    validStrings = ('any', 'main', 'contrib', 'non-free')

Debian = conf.registerPlugin('Debian')
conf.registerChannelValue(Debian, 'bold',
    registry.Boolean(True, _("""Determines whether the plugin will use bold in
    the responses to some of its commands.""")))
conf.registerGroup(Debian, 'defaults')
conf.registerChannelValue(Debian.defaults, 'branch',
    ValidBranch('stable', _("""Determines the default branch, ie. the branch
    selected if --branch is not given.""")))
conf.registerChannelValue(Debian.defaults, 'mode',
    ValidMode('path', _("""Determines the default mode, ie. the mode
    selected if --mode is not given.""")))
conf.registerChannelValue(Debian.defaults, 'section',
    ValidSection('any', _("""Determines the default section, ie. the section
    selected if --section is not given.""")))
conf.registerChannelValue(Debian.defaults, 'arch',
    registry.String('any', _("""Determines the default architecture,
    ie. the architecture selected if --arch is not given.""")))

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
