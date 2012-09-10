#!/usr/bin/env python
"""
twss.py - Jenni's That's What She Said Module
Copyright 2011 - Joel Friedly and Matt Meinwald
Licensed under the Eiffel Forum License 2.

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/

This module detects common phrases that many times can be responded with
"That's what she said."

It also allows users to add new "that's what she said" jokes to it's library
by following any appropriate statement with ".twss".
"""

import supybot.conf as conf
import urllib2
import re
import os
import sys

path = conf.supybot.directories.conf.dirize

last = "DEBUG_ME" # if you see this in the terminal, something broke.

if not os.path.exists(path('TWSS.txt')):
    with open(path('TWSS.txt'), "w") as f:
        with open(os.path.join(os.path.dirname(__file__), 'twss.txt'), 'r') as f2:
            f.write(f2.read())


def say_it(jenni, input):
    global last
    user_quotes = None
    with open(path('TWSS.txt')) as f:
        scraped_quotes = frozenset([line.rstrip() for line in f])
    if os.path.exists(path('TWSS.txt')):
        with open(path('TWSS.txt')) as f2:
            user_quotes = frozenset([line.rstrip() for line in f2])
    quotes = scraped_quotes.union(user_quotes) if user_quotes else scraped_quotes
    formatted = input.lower()
    if re.sub("[^\w\s]", "", formatted) in quotes:
        jenni.say("That's what she said.")
    last = re.sub("[^\w\s]", "", formatted)
say_it.rule = r"(.*)"
say_it.priority = "low"

def add_twss(jenni, input):
    print last
    with open(path('TWSS.txt'), "a") as f:
        f.write(re.sub(r"[^\w\s]", "", last.lower()) + "\n")
        f.close()
    jenni.say("That's what she said.")
add_twss.commands = ["twss"]
add_twss.priority = "low"
add_twss.threading = False

if __name__ == '__main__':
    print __doc__.strip()
