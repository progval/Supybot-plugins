###
# Copyright (c) 2005, James Vega
# Copyright (c) 2009-2010 Michael Tughan
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
import supybot.utils as utils
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('WunderWeather', True)

WunderWeather = conf.registerPlugin('WunderWeather')
conf.registerChannelValue(WunderWeather, 'imperial',
    registry.Boolean(True, """Shows imperial formatted data (Fahrenheit, miles/hour)
    in the weather output if true. You can have both imperial and metric enabled,
    and the bot will show both."""))
conf.registerChannelValue(WunderWeather, 'metric',
    registry.Boolean(True, """Shows metric formatted data (Celsius, kilometres/hour)
    in the weather output if true. You can have both imperial and metric enabled,
    and the bot will show both."""))
conf.registerChannelValue(WunderWeather, 'showPressure',
    registry.Boolean(True, """Determines whether the bot will show pressures in its
    output. The type of pressure shown will depend on the metric/imperial settings."""))
conf.registerChannelValue(WunderWeather, 'forecastDays',
    registry.NonNegativeInteger(0, """Determines how many days the forecast shows, up to 7.
    If set to 0, show all days. See showForecast configuration variable to turn off
    forecast display."""))
conf.registerChannelValue(WunderWeather, 'showCurrentByDefault',
    registry.Boolean(True, """If True, will show the current conditions in the weather
    output if no ouput control switches are given."""))
conf.registerChannelValue(WunderWeather, 'showForecastByDefault',
    registry.Boolean(True, """If True, will show the forecast in the weather
    output if no ouput control switches are given."""))

conf.registerUserValue(conf.users.plugins.WunderWeather, 'lastLocation',
    registry.String('', ''))


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
