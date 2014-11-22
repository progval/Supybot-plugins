A bunch of plugins for Supybot / Limnoria I either wrote myself or found on the
net and improved. Plugins that require HTTPd aren't compatible with 
Supybot or gribble. If you cannot load these plugins in Limnoria, please 
make sure you are using a recent version with the `version` command.

To install dependencies for Limnoria and these plugins, run

```
pip install -r https://raw.githubusercontent.com/ProgVal/Limnoria/master/requirements.txt
pip install -r requirements.txt
```

[![Build Status](https://travis-ci.org/ProgVal/Supybot-plugins.svg?branch=master)](https://travis-ci.org/ProgVal/Supybot-plugins)

## AttackProtector

Provides configurable flood protection for channels.

## AutoTrans

Sends in a query a translation of messages received in a channel.

## Brainfuck

Brainfuck (a turing-complete programming language) interpreter.

## ChannelStatus

Web interface for displaying channel-related data (topic, users, …)

## Coffee

Makes coffee for the channel.

## Debian

Grabs data from Debian's website.

## Eureka

Trivia plugin, with a new take on file design.

## GitHub

Plugin using the GitHub API & repo web hooks. **This plugin requires 
Limnoria**

## GoodFrench

French typo/spelling checker.

## IgnoreNonVoice

This plugin ignores users who aren't voiced. Can also be configured to 
only work when the channel is moderated `mode +m`. Useful with lesser 
moderation (`mode +z`).

## Iwant

Wishlist.

## Kickme

Utility plugin, useful in nested commands.

## LinkRelay

Highly configurable relay plugin.

## ListEmpty

List empty channels (or with few people) the bot is on.

## Listener

Run a telnet server and announce messages to a channel.

## OEIS

Graps data from the Online Encyclopedia of Integer Sequences.

## Pinglist

Keeps a list of people attending a meeting/game, and provides a `pingall`
command to ping them all.

## RateLimit

Provides rate-limiting of commands.

## Seeks

Plugin for the Seeks search engine.

## SupyML

Markup-based Supybot language supporting variables and loops.

## Trigger

Utility plugin that runs commands when a join/part/whatever occurs.

## Trivia

Trivia plugin.

## Twitter

Advanced Twitter plugin, with multiple account support.

## Untiny

URL unshortener plugin.

## WebLogs

Display channel logs on the web (experimental!). **This plugin requires 
Limnoria.**

## WebStats

Display channel stats on the web. **This plugin requires Limnoria.**

## WikiTrans

Translates words/expressions using Wikipedia inter-language links.

## Wikipedia

Wikipedia plugin.
