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
                      'supybot.plugins.Stocks.alphavantage.api.key', Raise=True)
        data = None
        try:
            data = requests.get('https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}'.format(symbol=symbol,
                api_key=api_key)).json()
            return data
        except Exception:
            raise

    def get_message(self, irc, symbol):
        # Do regex checking on symbol to ensure it's valid
        if not re.match('^[a-zA-Z]{1,6}$', symbol):
            irc.errorInvalid('symbol', symbol, Raise=True)

        # Get data from API
        data = self.get_symbol(irc, symbol)

        if not data:
            irc.error("{symbol}: An error occurred.".format(symbol=symbol), Raise=True)

        if 'Error Message' in data.keys():
            irc.error("{symbol}: {message}".format(symbol=symbol, message=data['Error Message']), Raise=True)

        symbol = data['Global Quote']['01. symbol']
        # open = data['Global Quote']['02. open']
        # high = data['Global Quote']['03. high']
        # low = data['Global Quote']['04. low']
        price = float(data['Global Quote']['05. price'])
        # volume = data['Global Quote']['06. volume']
        # latest_trading_day = data['Global Quote']['07. latest trading day']
        # previous_close = data['Global Quote']['08. previous close']
        change = float(data['Global Quote']['09. change'])
        change_percent = float(data['Global Quote']['10. change percent'].strip('%'))

        message = (
            '{symbol} {price:g} '
        )

        if change >= 0.0:
            message += ircutils.mircColor('\u25b2 {change:g} ({change_percent:g}%)', 'green')
        else:
            message += ircutils.mircColor('\u25bc {change:g} ({change_percent:g}%)', 'red')

        message = message.format(
            symbol=ircutils.bold(symbol),
            price=price,
            change=change,
            change_percent=change_percent,
        )

        return message

    @wrap([many('something')])
    def stock(self, irc, msg, args, symbols):
        """<symbol> [<symbol>, <symbol>, ...]

        Returns stock data for single or multiple symbols"""

        max_symbols = self.registryValue('alphavantage.maxsymbols')
        count_symbols = len(symbols)

        if count_symbols > max_symbols:
            irc.error("Too many symbols. Maximum count {}. Your count: {}".format(max_symbols, count_symbols), Raise=True)

        messages = map(lambda symbol: self.get_message(irc, symbol), symbols)

        irc.reply(' | '.join(messages))

Class = Stocks


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
