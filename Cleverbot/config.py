#!/usr/bin/env python
# CleverBot Supybot Plugin v1.0
# (C) Copyright 2012 Albert H. (alberthrocks)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
 
import supybot.conf as conf
import supybot.registry as registry
 
def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Cleverbot', True)
 
 
Cleverbot = conf.registerPlugin('Cleverbot')
#conf.registerGlobalValue(Cleverbot,'bot',registry.String('923c98f3de35606b',"""bot ID"""))
conf.registerGlobalValue(Cleverbot,'bot',registry.String('9c1423d9be345c5c',"""bot ID"""))
conf.registerGlobalValue(Cleverbot,'name',registry.String('AaronBot',"""bot name"""))
conf.registerChannelValue(Cleverbot,'react',registry.Boolean(True,"""Determine whether the bot should respond to errors."""))
conf.registerChannelValue(Cleverbot,'reactprivate',registry.Boolean(True,"""Determine whether the bot should respond to private chat errors."""))
conf.registerChannelValue(Cleverbot,'enable',registry.Boolean(False,"""Determine whether the Cleverbot response is enabled or not"""))
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Cleverbot, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))
 
 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79: