###
# Copyright (c) 2017 Rusty Bower
# Copyright (c) 2020 Valentin Lorentz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###

import re
import requests
from datetime import datetime, timedelta

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Stocks')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Stocks(callbacks.Plugin):
    """Provides access to stocks data"""
    threaded = True

    def get_symbol(self, irc, symbol):
        api_key = self.registryValue('alphavantage.api.key')
        if not api_key:
            irc.error('Missing API key, ask the admin to get one and set '
                      'supybot.plugins.alphavantage.api.key', Raise=True)
        data = None
        try:
            data = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'.format(symbol=symbol,
                api_key=api_key)).json()
            return data
        except Exception:
            raise


    @wrap(['somethingWithoutSpaces'])
    def stock(self, irc, msg, args, symbol):
        """<symbol>

        Returns stock data for <symbol>."""
        # Do regex checking on symbol to ensure it's valid
        if not re.match('^[a-zA-Z]{1,5}$', symbol):
            irc.errorInvalid('symbol', symbol, Raise=True)

        # Get data from API
        data = self.get_symbol(irc, symbol)

        if not data:
            irc.error("An error occurred.", Raise=True)

        if 'Error Message' in data.keys():
            irc.error(data['Error Message'], Raise=True)

        days = sorted(data['Time Series (Daily)'].keys(), reverse=True)

        # Only 1 day of history, likely this is a new stock on the market
        if len(days) == 1:
            today = days[0]
            close = data['Time Series (Daily)'][today]['4. close']
            prevclose = data['Time Series (Daily)'][today]['1. open']
        else:
            # Get today's entry
            today = days[0]
            prevdate = days[1]

            # dict_keys(['1. open', '2. high', '3. low', '4. close', '5. volume'])
            # open = data['Time Series (Daily)'][today]['1. open']
            # high = data['Time Series (Daily)'][today]['2. high']
            # low = data['Time Series (Daily)'][today]['3. low']
            close = data['Time Series (Daily)'][today]['4. close']
            # volume = data['Time Series (Daily)'][today]['5. volume']

            # Get yesterday's close
            prevclose = data['Time Series (Daily)'][prevdate]['4. close']

        # Calculate change
        change = float(close) - float(prevclose)

        # Calculate percentage change
        percentchange = float(change) / float(prevclose) * 100

        message = (
            '{symbol} ${close:g} '
        )

        if change >= 0:
            message += ircutils.mircColor('{change:g} ({percentchange:.2f}%) \u2b06', 'green')
        else:
            message += ircutils.mircColor('{change:g} ({percentchange:.2f}%) \u2b07', 'red')

        message = message.format(
            symbol=data['Meta Data']['2. Symbol'].upper(),
            close=float(close),
            change=float(change),
            percentchange=float(percentchange),
        )

        # Print results to channel
        irc.reply(message)


Class = Stocks


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
