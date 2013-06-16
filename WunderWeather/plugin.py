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

import sys
import xml.dom.minidom as dom

import supybot.utils as utils
from supybot.commands import wrap, additional, getopts
import supybot.callbacks as callbacks

from . import shortforms

# Name 'reload' is used by Supybot
from imp import reload as reload_
reload_(shortforms)

if sys.version_info[0] >= 3:
    def u(s):
        return s
else:
    def u(s):
        return unicode(s, "unicode_escape")

noLocationError = 'No such location could be found.'
class NoLocation(callbacks.Error):
    pass

class WunderWeather(callbacks.Plugin):
    """Uses the Wunderground XML API to get weather conditions for a given location.
    Always gets current conditions, and by default shows a 7-day forecast as well."""
    threaded = True
    
    
    ##########    GLOBAL VARIABLES    ##########
    
    _weatherCurrentCondsURL = 'http://api.wunderground.com/auto/wui/geo/WXCurrentObXML/index.xml?query=%s'
    _weatherForecastURL = 'http://api.wunderground.com/auto/wui/geo/ForecastXML/index.xml?query=%s'
    
    
    ##########    EXPOSED METHODS    ##########
    
    def weather(self, irc, msg, args, options, location):
        """[--current|--forecast|--all] [US zip code | US/Canada city, state | Foreign city, country]

        Returns the approximate weather conditions for a given city from Wunderground.
        --current, --forecast, and --all control what kind of information the command
        shows.
        """
        matchedLocation = self._commandSetup(irc, msg, location)
        locationName = self._getNodeValue(matchedLocation[0], 'full', 'Unknown Location')
        
        output = []
        showCurrent = False
        showForecast = False
        
        if not options:
            # use default output
            showCurrent = self.registryValue('showCurrentByDefault', self.__channel)
            showForecast = self.registryValue('showForecastByDefault', self.__channel)
        else:
            for (type, arg) in options:
                if type == 'current':
                    showCurrent = True
                elif type == 'forecast':
                    showForecast = True
                elif type == 'all':
                    showCurrent = True
                    showForecast = True
        
        if showCurrent and showForecast:
            output.append(u('Weather for ') + locationName)
        elif showCurrent:
            output.append(u('Current weather for ') + locationName)
        elif showForecast:
            output.append(u('Forecast for ') + locationName)
        
        if showCurrent:
            output.append(self._getCurrentConditions(matchedLocation[0]))
        
        if showForecast:
            # _getForecast returns a list, so we have to call extend rather than append
            output.extend(self._getForecast(matchedLocation[1]))
        
        if not showCurrent and not showForecast:
            irc.error("Something weird happened... I'm not supposed to show current conditions or a forecast!")
        
        irc.reply(self._formatUnicodeOutput(output))
    weather = wrap(weather, [getopts({'current': '', 'forecast': '', 'all': ''}), additional('text')])
    
    
    ##########    SUPPORTING METHODS    ##########
    
    def _checkLocation(self, location):
        if not location:
            location = self.userValue('lastLocation', self.__msg.prefix)
        if not location:
            raise callbacks.ArgumentError
        self.setUserValue('lastLocation', self.__msg.prefix, location, ignoreNoUser=True)
        
        # Check for shortforms, because Wunderground will attempt to check
        # for US locations without a full country name.
        
        # checkShortforms may return Unicode characters in the country name.
        # Need Latin 1 for Supybot's URL handlers to work
        webLocation = shortforms.checkShortforms(location)
        conditions = self._getDom(self._weatherCurrentCondsURL % utils.web.urlquote(webLocation))
        observationLocation = conditions.getElementsByTagName('observation_location')[0]
        
        # if there's no city name in the XML, we didn't get a match
        if observationLocation.getElementsByTagName('city')[0].childNodes.length < 1:
            # maybe the country shortform given conflicts with a state shortform and wasn't replaced before
            webLocation = shortforms.checkConflictingShortforms(location)
            
            # if no conflicting short names match, we have the same query as before
            if webLocation == None:
                return None
            
            conditions = self._getDom(self._weatherCurrentCondsURL % utils.web.urlquote(webLocation))
            observationLocation = conditions.getElementsByTagName('observation_location')[0]
            
            # if there's still no match, nothing more we can do
            if observationLocation.getElementsByTagName('city')[0].childNodes.length < 1:
                return None
        
        # if we get this far, we got a match. Return the DOM and location
        return (conditions, webLocation)
    
    def _commandSetup(self, irc, msg, location):
        channel = None
        if irc.isChannel(msg.args[0]):
            channel = msg.args[0]
        
        # set various variables for submethods use
        self.__irc = irc
        self.__msg = msg
        self.__channel = channel
        
        matchedLocation = self._checkLocation(location)
        if not matchedLocation:
            self._noLocation()
        
        return matchedLocation
    
    # format temperatures using _formatForMetricOrImperial
    def _formatCurrentConditionTemperatures(self, dom, string):
        tempC = self._getNodeValue(dom, string + '_c', u('N/A')) + u('\xb0C')
        tempF = self._getNodeValue(dom, string + '_f', u('N/A')) + u('\xb0F')
        return self._formatForMetricOrImperial(tempF, tempC)
    
    def _formatForecastTemperatures(self, dom, type):
        tempC = self._getNodeValue(dom.getElementsByTagName(type)[0], 'celsius', u('N/A')) + u('\xb0C')
        tempF = self._getNodeValue(dom.getElementsByTagName(type)[0], 'fahrenheit', u('N/A')) + u('\xb0F')
        return self._formatForMetricOrImperial(tempF, tempC)
    
    # formats any imperial or metric values according to the config
    def _formatForMetricOrImperial(self, imperial, metric):
        returnValues = []
        
        if self.registryValue('imperial', self.__channel):
            returnValues.append(imperial)
        if self.registryValue('metric', self.__channel):
            returnValues.append(metric)
        
        if not returnValues:
            returnValues = (imperial, metric)
        
        return u(' / ').join(returnValues)
    
    def _formatPressures(self, dom):
        # lots of function calls, but it just divides pressure_mb by 10 and rounds it
        pressureKpa = str(round(float(self._getNodeValue(dom, 'pressure_mb', u('0'))) / 10, 1)) + 'kPa'
        pressureIn = self._getNodeValue(dom, 'pressure_in', u('0')) + 'in'
        return self._formatForMetricOrImperial(pressureIn, pressureKpa)
    
    def _formatSpeeds(self, dom, string):
        mphValue = float(self._getNodeValue(dom, string, u('0')))
        speedM = u('%dmph') % round(mphValue)
        speedK = u('%dkph') % round(mphValue * 1.609344) # thanks Wikipedia for the conversion rate
        return self._formatForMetricOrImperial(speedM, speedK)
    
    def _formatUpdatedTime(self, dom):
        observationTime = self._getNodeValue(dom, 'observation_epoch', None)
        localTime = self._getNodeValue(dom, 'local_epoch', None)
        if not observationTime or not localTime:
            return self._getNodeValue(dom, 'observation_time', 'Unknown Time').lstrip(u('Last Updated on '))
        
        seconds = int(localTime) - int(observationTime)
        minutes = int(seconds / 60)
        seconds -= minutes * 60
        hours = int(minutes / 60)
        minutes -= hours * 60
        
        if seconds == 1:
            seconds = '1 sec'
        else:
            seconds = '%d secs' % seconds
        
        if minutes == 1:
            minutes = '1 min'
        else:
            minutes = '%d mins' % minutes
        
        if hours == 1:
            hours = '1 hr'
        else:
            hours = '%d hrs' % hours
        
        if hours == '0 hrs':
            if minutes == '0 mins':
                return '%s ago' % seconds
            return '%s, %s ago' % (minutes, seconds)
        return '%s, %s, %s ago' % (hours, minutes, seconds)
    
    def _getCurrentConditions(self, dom):
        output = []
        
        temp = self._formatCurrentConditionTemperatures(dom, 'temp')
        if self._getNodeValue(dom, 'heat_index_string') != 'NA':
            temp += u(' (Heat Index: %s)') % self._formatCurrentConditionTemperatures(dom, 'heat_index')
        if self._getNodeValue(dom, 'windchill_string') != 'NA':
            temp += u(' (Wind Chill: %s)') % self._formatCurrentConditionTemperatures(dom, 'windchill')
        output.append(u('Temperature: ') + temp)
        
        output.append(u('Humidity: ') + self._getNodeValue(dom, 'relative_humidity', u('N/A%')))
        if self.registryValue('showPressure', self.__channel):
            output.append(u('Pressure: ') + self._formatPressures(dom))
        output.append(u('Conditions: ') + self._getNodeValue(dom, 'weather').capitalize())
        output.append(u('Wind: ') + self._getNodeValue(dom, 'wind_dir', u('None')).capitalize() + ', ' + self._formatSpeeds(dom, 'wind_mph'))
        output.append(u('Updated: ') + self._formatUpdatedTime(dom))
        return u('; ').join(output)
    
    def _getDom(self, url):
        try:
            xmlString = utils.web.getUrl(url)
            return dom.parseString(xmlString)
        except utils.web.Error as e:
            error = e.args[0].capitalize()
            if error[-1] != '.':
                error = error + '.'
            self.__irc.error(error, Raise=True)
    
    def _getForecast(self, location):
        dom = self._getDom(self._weatherForecastURL % utils.web.urlquote(location))
        output = []
        count = 0
        max = self.registryValue('forecastDays', self.__channel)
        
        forecast = dom.getElementsByTagName('simpleforecast')[0]
        
        for day in forecast.getElementsByTagName('forecastday'):
            if count >= max and max != 0:
                break
            forecastOutput = []
            
            forecastOutput.append('Forecast for ' + self._getNodeValue(day, 'weekday').capitalize() + ': ' + self._getNodeValue(day, 'conditions').capitalize())
            forecastOutput.append('High of ' + self._formatForecastTemperatures(day, 'high'))
            forecastOutput.append('Low of ' + self._formatForecastTemperatures(day, 'low'))
            output.append('; '.join(forecastOutput))
            count += 1
        
        return output
    
    
    ##########    STATIC METHODS    ##########
    
    def _formatUnicodeOutput(output):
        # UTF-8 encoding is required for Supybot to handle \xb0 (degrees) and other special chars
        # We can't (yet) pass it a Unicode string on its own (an oddity, to be sure)
        s = u(' | ').join(output)
        if sys.version_info[0] < 3:
            s = s.encode('utf-8')
        return s
    _formatUnicodeOutput = staticmethod(_formatUnicodeOutput)
    
    def _getNodeValue(dom, value, default=u('Unknown')):
        subTag = dom.getElementsByTagName(value)
        if len(subTag) < 1:
            return default
        subTag = subTag[0].firstChild
        if subTag == None:
            return default
        return subTag.nodeValue
    _getNodeValue = staticmethod(_getNodeValue)
    
    def _noLocation():
        raise NoLocation(noLocationError)
    _noLocation = staticmethod(_noLocation)

Class = WunderWeather

