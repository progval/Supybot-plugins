# coding=utf-8
import re
import requests
from datetime import datetime, timedelta
from sopel.config.types import NO_DEFAULT, StaticSection, ValidatedAttribute
from sopel.formatting import color, colors
from sopel.logger import get_logger
from sopel.module import commands, example, NOLIMIT

logger = get_logger(__name__)


# Define our sopel stocks configuration
class StocksSection(StaticSection):
    api_key = ValidatedAttribute('api_key', default=NO_DEFAULT)


def setup(bot):
    bot.config.define_section('stocks', StocksSection)


# Walk the user through defining variables required
def configure(config):
    config.define_section('stocks', StocksSection, validate=False)
    config.stocks.configure_setting(
        'api_key',
        'Enter AlphaVantage API Key:'
    )


def get_symbol(bot, symbol):
    data = None
    try:
        data = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'.format(symbol=symbol, api_key=bot.config.stocks.api_key)).json()
        return data
    except Exception:
        raise


@commands('stock')
@example('.stock msft')
def stock(bot, trigger):
    # If the user types .stock with no arguments, let them know proper usage
    if not trigger.group(2):
        return
    else:
        # Get symbol
        symbol = trigger.group(2)

        # Do regex checking on symbol to ensure it's valid
        if not re.match('^[a-zA-Z]{1,5}$', symbol):
            bot.say('Invalid Symbol')
            return

        # Get data from API
        data = get_symbol(bot, symbol)

        if not data:
            bot.say("An error occurred.")
            return

        if 'Error Message' in data.keys():
            logger.error(data['Error Message'])
            return

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
            message += color('{change:g} ({percentchange:.2f}%)', colors.GREEN)
            message += color(u'\u2b06', colors.GREEN)
        else:
            message += color('{change:g} ({percentchange:.2f}%)', colors.RED)
            message += color(u'\u2b07', colors.RED)

        message = message.format(
            symbol=data['Meta Data']['2. Symbol'].upper(),
            close=float(close),
            change=float(change),
            percentchange=float(percentchange),
        )

        # Print results to channel
        bot.say(message)
